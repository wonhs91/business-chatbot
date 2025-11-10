# Chat Widget

Embeddable TypeScript widget that connects the website to the LangGraph backend.

## Development

```bash
npm install
npm run dev
```

The dev command bundles the widget in watch mode to `dist/index.js` using `tsup`.

## Build

```bash
npm run build
```

This produces a minified `dist/index.js` file exposing a global `BusinessChatWidget` object.

## Embedding on WordPress

1. Host `dist/index.js` (and optionally a sourcemap) on your CDN or WordPress theme assets.
2. Add the following snippet to the site footer or appropriate HTML block:

```html
<script src="https://yourcdn.com/chat-widget/index.js" defer></script>
<script>
  window.addEventListener("DOMContentLoaded", function () {
    window.BusinessChatWidget?.init({
      baseUrl: "https://api.yourdomain.com",
      title: "Hi there!",
      placeholder: "Ask us anything about our services",
      primaryColor: "#2563eb"
    });
  });
</script>
```

Configure `baseUrl` to match the deployment URL of the FastAPI backend.

