# Python UI Kit Crawler Base Image

Erweitert `python_basic_crawler` um das gemeinsame Goslar UI-Kit unter `/app/ui-kit`.

## Enthaltene Dateien

- `goslar-ui.css`: Design Tokens, Seitenlayout und Komponenten.
- `goslar-ui.js`: Optionales Such-/Filterverhalten über `data-gs-search`.
- `example.html`: Referenzseite für Header, Suche, Widget, Button und Info-Card.

## Verwendung in Crawlern

Crawler mit HTML-Seiten verwenden dieses Image als Base:

```dockerfile
FROM ghcr.io/machmitgoslar/gs_crawler_python_ui_kit_crawler:latest
```

Im HTML wird das UI-Kit aus dem Output geladen:

```html
<link rel="stylesheet" href="ui-kit/goslar-ui.css" />
```

Das Crawler-Script kopiert die Dateien aus `/app/ui-kit` nach `/app/output/ui-kit`.

## Komponenten

- `gs-page`, `gs-page--with-back`
- `gs-page-header`, `gs-page-title`, `gs-page-description`
- `gs-back-link`
- `gs-search`
- `gs-widget`
- `gs-button-card`
- `gs-info-card`
- `gs-actions`, `gs-action`
