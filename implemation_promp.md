## Setting

### API
We have an oauth/oicd guarded api endpoint at 'https://hsp-organisations-linux-preview-fpc4agc2fsb5d6ch.westeurope-01.azurewebsites.net/api/'
You'll find the Openapi documentation at https://hsp-organisations-linux-preview-fpc4agc2fsb5d6ch.westeurope-01.azurewebsites.net/swagger/v1/swagger.json 

#### Markets API Endpoint
https://hsp-external-gateway-linux-cfethubabxayf7aq.westeurope-01.azurewebsites.net/api/external/market-events/upcoming 

https://hsp-external-gateway-linux-cfethubabxayf7aq.westeurope-01.azurewebsites.net/api/external/market-events/{id}/attendances 


### Auth
For out implemantion task we have the following credentials to implement a client_credential workflow
- client_id: gmg.client
- client_secret: 0uAQBew9XARxC90D
- scope: markets.read
- https://backend.goslar-id.ceconsoft.de/connect/token

### Goal & Aim
- We need an up-to-date list of market attendes presented in the Frontend App. The interface of the App consists of the following parts
-- Card and Main JSON
´´´
    {
        "title": "Schmücken des Immenröder Weihnachtsbaums",
        "description": "Schmücken des Immenröder Weihnachtsbaums 29.11.2025 15:00 bis 16:30 auf dem Immenröder Dorfplatz. Wir schmücken mit selbst mitgebrachten Kugeln und selbst gebasteltem Schmuck. Zum leiblichen Wohl bieten wir: Weißer Glühwein, Kakao und Kaffee gegen Spenden....",
        "image_url": "https://immenro.de/wp-content/uploads/2025/11/Immernoeder-Weihnachtsbaum-980x450.png",
        "call_to_action_url": "https://immenro.de/schmuecken-des-immenroeder-weihnachtsbaums",
        "published_at": "2026-01-19T10:32"
    }
´´´ 
-- Index
´´´
    [
    {
        "id": 1
        "title": "Schmücken des Immenröder Weihnachtsbaums",
        "description": "Schmücken des Immenröder Weihnachtsbaums 29.11.2025 15:00 bis 16:30 auf dem Immenröder Dorfplatz. Wir schmücken mit selbst mitgebrachten Kugeln und selbst gebasteltem Schmuck. Zum leiblichen Wohl bieten wir: Weißer Glühwein, Kakao und Kaffee gegen Spenden....",
        "image_url": "https://immenro.de/wp-content/uploads/2025/11/Immernoeder-Weihnachtsbaum-980x450.png",
        "call_to_action_url": "https://immenro.de/schmuecken-des-immenroeder-weihnachtsbaums",
        "published_at": "2026-01-19T10:32"
    },
    ]
´´´

Detail View
´´´
    {
    "id": 2,
    "title": "Meldung 2",
    "summary": "Zusammenfassung",
    "description": "<p>Dies ist eine <strong>Beschreibung</strong></p>",
    "images": [
        {
        "url": "http://external.com/image-url-1.jpg"
        },
        {
        "url": "http://external.com/image-url-2.jpg"
        }
    ],
    "call_to_action_url": "http://external.com/webview-url-2",
    "published_at": "2024-12-05T13:45"
    }
´´´

- We need to aggregate the data to have an up-to-date data endpoint. The main json will be the interface for the app. The call_to_action_urls will translate from the main view to the respective index (list view) and from there on to the detail view. 

- My wish for presentation
-- The Card should show an image with a presentation of the next market. With the cta "Alle Stände im Blick..."
-- The index should present all the vendors for this market
-- the detail card should present the vendor and link to his website (if present)
- Develop an own docker container in the environemt we are having. Try to utilize aspects we already implemented to keep the maintainance minimal

