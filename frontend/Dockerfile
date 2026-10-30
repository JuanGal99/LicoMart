# 1. Etapa de build (Node)
FROM node:20 AS build

WORKDIR /app

# Copiar package.json y package-lock.json / pnpm-lock / yarn.lock
COPY package*.json ./
# Si usas pnpm/yarn, ajusta el comando:
RUN npm install

# Copiar el código
COPY . .

# Hacer el build de producción
RUN npm run build

# 2. Etapa de producción (Nginx)
FROM nginx:stable-alpine

# Copiamos el build al directorio que sirve nginx
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer el puerto
EXPOSE 80

# Nginx arranca por defecto con este CMD en la imagen base
