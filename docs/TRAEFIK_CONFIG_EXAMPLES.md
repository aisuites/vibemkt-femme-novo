# EXEMPLOS DE CONFIGURAÇÃO - TRAEFIK

**Data:** 09/02/2026  
**Versão:** 1.0

---

## 📁 ESTRUTURA DE ARQUIVOS

**IMPORTANTE:** Este servidor usa configuração via `command` no docker-compose.yml, NÃO arquivos separados.

```
/opt/traefik/
├── docker-compose.yml    # Configuração via command
├── .env                  # Variáveis de ambiente
├── letsencrypt/
│   └── acme.json        # Certificados SSL
└── oauth2/
    └── authenticated-emails.txt
```

---

## 🐳 DOCKER COMPOSE

**Arquivo:** `/opt/apps/traefik/docker-compose.yml`

### Configuração Atual do Servidor (via Command)

**Arquivo:** `/opt/traefik/docker-compose.yml`

```yaml
version: "3.9"

services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    command:
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --providers.docker.endpoint=unix:///var/run/docker.sock
      
      # Entrypoints HTTP/HTTPS
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      
      # Redirecionar tudo de HTTP -> HTTPS
      - --entrypoints.web.http.redirections.entryPoint.to=websecure
      - --entrypoints.web.http.redirections.entryPoint.scheme=https
      
      # Let's Encrypt via Cloudflare DNS-01
      - --certificatesresolvers.cloudflare.acme.dnschallenge=true
      - --certificatesresolvers.cloudflare.acme.dnschallenge.provider=cloudflare
      - --certificatesresolvers.cloudflare.acme.email=${ACME_EMAIL}
      - --certificatesresolvers.cloudflare.acme.storage=/letsencrypt/acme.json
      
      # Logs
      - --log.level=INFO
    
    ports:
      - "80:80"
      - "443:443"
    
    environment:
      - CF_DNS_API_TOKEN=${CF_DNS_API_TOKEN}
    
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/traefik/letsencrypt:/letsencrypt
    
    networks:
      - traefik_proxy
    
    restart: always

networks:
  traefik_proxy:
    external: true
```

**Arquivo:** `/opt/traefik/.env`

```bash
# Email para Let's Encrypt
ACME_EMAIL=seu-email@dominio.com

# Cloudflare API Token (para DNS Challenge)
CF_DNS_API_TOKEN=seu-cloudflare-token
```

### Com Portainer + OAuth2 (Configuração Completa Atual)

**Arquivo:** `/opt/traefik/docker-compose.yml`

```yaml
version: "3.9"

services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    command:
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --providers.docker.endpoint=unix:///var/run/docker.sock
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --entrypoints.web.http.redirections.entryPoint.to=websecure
      - --entrypoints.web.http.redirections.entryPoint.scheme=https
      - --certificatesresolvers.cloudflare.acme.dnschallenge=true
      - --certificatesresolvers.cloudflare.acme.dnschallenge.provider=cloudflare
      - --certificatesresolvers.cloudflare.acme.email=${ACME_EMAIL}
      - --certificatesresolvers.cloudflare.acme.storage=/letsencrypt/acme.json
      - --log.level=INFO
    ports:
      - "80:80"
      - "443:443"
    environment:
      - CF_DNS_API_TOKEN=${CF_DNS_API_TOKEN}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/traefik/letsencrypt:/letsencrypt
    networks:
      - traefik_proxy
    restart: always

  oauth2-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:latest
    container_name: oauth2_proxy
    command:
      - --provider=google
      - --email-domain=example.invalid
      - --authenticated-emails-file=/etc/oauth2/authenticated-emails.txt
      - --upstream=http://portainer:9000
      - --http-address=0.0.0.0:4180
      - --cookie-secure=true
      - --cookie-domain=portainer-femmeintegra.aisuites.com.br
      - --whitelist-domain=portainer-femmeintegra.aisuites.com.br
      - --redirect-url=https://portainer-femmeintegra.aisuites.com.br/oauth2/callback
    environment:
      - OAUTH2_PROXY_CLIENT_ID=${OAUTH2_PROXY_CLIENT_ID}
      - OAUTH2_PROXY_CLIENT_SECRET=${OAUTH2_PROXY_CLIENT_SECRET}
      - OAUTH2_PROXY_COOKIE_SECRET=${OAUTH2_PROXY_COOKIE_SECRET}
    networks:
      - traefik_proxy
    restart: always
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.oauth.entrypoints=websecure"
      - "traefik.http.routers.oauth.rule=Host(`portainer-femmeintegra.aisuites.com.br`)"
      - "traefik.http.routers.oauth.tls.certresolver=cloudflare"
      - "traefik.http.services.oauth.loadbalancer.server.port=4180"
    volumes:
      - /opt/traefik/oauth2/authenticated-emails.txt:/etc/oauth2/authenticated-emails.txt:ro

  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    command: -H unix:///var/run/docker.sock
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    networks:
      - traefik_proxy
    restart: always

networks:
  traefik_proxy:
    external: true

volumes:
  portainer_data:
    external: true
```

---

## ⚙️ CONFIGURAÇÃO VIA COMMAND

**IMPORTANTE:** Este servidor NÃO usa arquivos `traefik.yml` ou `dynamic.yml`. Toda configuração é feita via `command` no docker-compose.yml.

### Exemplo de Configuração Antiga (NÃO USAR)

~~**Arquivo:** `/opt/traefik/config/traefik.yml`~~

### Desenvolvimento (HTTP + Dashboard)

```yaml
# Traefik Static Configuration - Development
api:
  dashboard: true
  insecure: true  # Dashboard sem autenticação (apenas dev!)

entryPoints:
  web:
    address: ":80"
  
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: traefik_proxy
  
  file:
    filename: /dynamic.yml
    watch: true

log:
  level: INFO
  format: common

accessLog:
  format: common
```

### Produção (HTTPS + Let's Encrypt)

```yaml
# Traefik Static Configuration - Production
api:
  dashboard: true
  insecure: false  # Dashboard protegido

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  
  websecure:
    address: ":443"
    http:
      tls:
        certResolver: letsencrypt

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: traefik_proxy
  
  file:
    filename: /dynamic.yml
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: seu-email@dominio.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

log:
  level: INFO
  format: json
  filePath: /var/log/traefik/traefik.log

accessLog:
  format: json
  filePath: /var/log/traefik/access.log
  filters:
    statusCodes:
      - "400-599"
```

### Produção com Cloudflare DNS Challenge

```yaml
# Traefik Static Configuration - Production + Cloudflare
api:
  dashboard: true
  insecure: false

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  
  websecure:
    address: ":443"
    http:
      tls:
        certResolver: cloudflare

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: traefik_proxy
  
  file:
    filename: /dynamic.yml
    watch: true

certificatesResolvers:
  cloudflare:
    acme:
      email: seu-email@dominio.com
      storage: /letsencrypt/acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
          - "8.8.8.8:53"

log:
  level: INFO
  format: json

accessLog:
  format: json
```

---

## 🔧 MIDDLEWARES E SEGURANÇA

**IMPORTANTE:** Middlewares podem ser configurados via labels nos containers ou via command.

### Via Labels (Recomendado para este servidor)

### Básica

```yaml
# Traefik Dynamic Configuration
http:
  middlewares:
    # Redirecionamento HTTPS
    https-redirect:
      redirectScheme:
        scheme: https
        permanent: true
    
    # Headers de segurança
    security-headers:
      headers:
        frameDeny: true
        sslRedirect: true
        browserXssFilter: true
        contentTypeNosniff: true
        forceSTSHeader: true
        stsIncludeSubdomains: true
        stsPreload: true
        stsSeconds: 31536000
        customFrameOptionsValue: "SAMEORIGIN"

tls:
  options:
    default:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
```

### Avançada (com Rate Limiting e Compressão)

```yaml
# Traefik Dynamic Configuration - Advanced
http:
  middlewares:
    # Redirecionamento HTTPS
    https-redirect:
      redirectScheme:
        scheme: https
        permanent: true
    
    # Headers de segurança
    security-headers:
      headers:
        frameDeny: true
        sslRedirect: true
        browserXssFilter: true
        contentTypeNosniff: true
        forceSTSHeader: true
        stsIncludeSubdomains: true
        stsPreload: true
        stsSeconds: 31536000
        customFrameOptionsValue: "SAMEORIGIN"
        customResponseHeaders:
          X-Robots-Tag: "noindex,nofollow,nosnippet,noarchive,notranslate,noimageindex"
          server: ""
    
    # Rate Limiting
    rate-limit:
      rateLimit:
        average: 100
        burst: 50
        period: 1m
    
    # Compressão
    compression:
      compress: {}
    
    # Autenticação básica (exemplo)
    auth:
      basicAuth:
        users:
          - "admin:$apr1$xyz..."  # Gerar com: htpasswd -nb admin senha

tls:
  options:
    default:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
      curvePreferences:
        - CurveP521
        - CurveP384
```

---

## 🔐 GERAR SENHA PARA AUTENTICAÇÃO BÁSICA

```bash
# Instalar htpasswd
sudo apt install apache2-utils

# Gerar senha
htpasswd -nb admin sua-senha

# Resultado (copiar para dynamic.yml):
# admin:$apr1$xyz...
```

---

## 🌐 LABELS DO DOCKER COMPOSE (IAMKT)

### Configuração Básica

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=traefik_proxy"
  
  # HTTP → HTTPS redirect
  - "traefik.http.routers.iamkt-http.rule=Host(`iamkt.seu-dominio.com`)"
  - "traefik.http.routers.iamkt-http.entrypoints=web"
  - "traefik.http.routers.iamkt-http.middlewares=https-redirect"
  
  # HTTPS
  - "traefik.http.routers.iamkt-https.rule=Host(`iamkt.seu-dominio.com`)"
  - "traefik.http.routers.iamkt-https.entrypoints=websecure"
  - "traefik.http.routers.iamkt-https.tls=true"
  
  # Service
  - "traefik.http.services.iamkt.loadbalancer.server.port=8000"
```

### Com Let's Encrypt

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=traefik_proxy"
  
  # HTTP → HTTPS redirect
  - "traefik.http.routers.iamkt-http.rule=Host(`iamkt.seu-dominio.com`)"
  - "traefik.http.routers.iamkt-http.entrypoints=web"
  - "traefik.http.routers.iamkt-http.middlewares=https-redirect"
  
  # HTTPS
  - "traefik.http.routers.iamkt-https.rule=Host(`iamkt.seu-dominio.com`)"
  - "traefik.http.routers.iamkt-https.entrypoints=websecure"
  - "traefik.http.routers.iamkt-https.tls=true"
  - "traefik.http.routers.iamkt-https.tls.certresolver=letsencrypt"
  
  # Service
  - "traefik.http.services.iamkt.loadbalancer.server.port=8000"
```

### Com Middlewares Adicionais

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=traefik_proxy"
  
  # HTTP → HTTPS redirect
  - "traefik.http.routers.iamkt-http.rule=Host(`iamkt.seu-dominio.com`)"
  - "traefik.http.routers.iamkt-http.entrypoints=web"
  - "traefik.http.routers.iamkt-http.middlewares=https-redirect"
  
  # HTTPS
  - "traefik.http.routers.iamkt-https.rule=Host(`iamkt.seu-dominio.com`)"
  - "traefik.http.routers.iamkt-https.entrypoints=websecure"
  - "traefik.http.routers.iamkt-https.tls=true"
  - "traefik.http.routers.iamkt-https.tls.certresolver=cloudflare"
  - "traefik.http.routers.iamkt-https.middlewares=security-headers,compression,rate-limit"
  
  # Service
  - "traefik.http.services.iamkt.loadbalancer.server.port=8000"
```

### Múltiplos Domínios

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=traefik_proxy"
  
  # HTTP
  - "traefik.http.routers.iamkt-http.rule=Host(`iamkt.com`) || Host(`www.iamkt.com`)"
  - "traefik.http.routers.iamkt-http.entrypoints=web"
  - "traefik.http.routers.iamkt-http.middlewares=https-redirect"
  
  # HTTPS
  - "traefik.http.routers.iamkt-https.rule=Host(`iamkt.com`) || Host(`www.iamkt.com`)"
  - "traefik.http.routers.iamkt-https.entrypoints=websecure"
  - "traefik.http.routers.iamkt-https.tls=true"
  - "traefik.http.routers.iamkt-https.tls.certresolver=letsencrypt"
  
  # Service
  - "traefik.http.services.iamkt.loadbalancer.server.port=8000"
```

---

## 🚀 COMANDOS ÚTEIS

```bash
# Iniciar Traefik
cd /opt/traefik
docker compose up -d

# Ver logs
docker logs traefik -f

# Verificar configuração
docker exec traefik traefik version

# Reiniciar
docker compose restart

# Parar
docker compose down

# Verificar certificados Let's Encrypt
sudo cat /opt/traefik/letsencrypt/acme.json | jq

# Testar SSL
curl -I https://seu-dominio.com
openssl s_client -connect seu-dominio.com:443 -servername seu-dominio.com
```

---

## 🔍 TROUBLESHOOTING

### Dashboard não acessível

```bash
# Verificar se está rodando
docker ps | grep traefik

# Verificar logs
docker logs traefik

# Verificar porta
netstat -tuln | grep 8080
```

### Certificado SSL não gerado

```bash
# Verificar logs
docker logs traefik | grep -i acme

# Verificar arquivo acme.json
ls -lah /opt/traefik/letsencrypt/acme.json

# Permissões corretas
sudo chmod 600 /opt/traefik/letsencrypt/acme.json

# Limpar e tentar novamente
sudo rm /opt/traefik/letsencrypt/acme.json
cd /opt/traefik
docker compose restart
```

### Aplicação não acessível

```bash
# Verificar rede
docker network inspect traefik_proxy

# Verificar labels
docker inspect iamkt_web | grep traefik

# Verificar se aplicação está na rede
docker network inspect traefik_proxy | grep iamkt_web
```

---

## 📚 REFERÊNCIAS

- [Documentação Oficial Traefik](https://doc.traefik.io/traefik/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Cloudflare DNS](https://www.cloudflare.com/)

---

**Última atualização:** 09/02/2026
