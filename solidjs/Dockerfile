# Serves the prebuilt SPA (run `npm run build` first).
FROM nginx:1.27-alpine
COPY nginx.cloudrun.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html/
EXPOSE 8080
