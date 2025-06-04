<?php

/**
 * Fetches all issues of "Seniorenzeitung" von goslar.de/leben-in-goslar/seniorenzeitung and updates ../httpdocs/senioren/feed.xml
 * @var $url - Where to fetch
 * @var $file_path - Where to check old feed and update
 */

$url = "https://www.goslar.de/leben-in-goslar/senioren/seniorenzeitung";
$file_path = "../httpdocs/senioren/feed.xml";


// Webseite abrufen
$html = @file_get_contents($url);
if ($html === false) {
    die("Fehler beim Laden der Seite.");
}


// HTML parsen
libxml_use_internal_errors(true);
$dom = new DOMDocument();
$dom->loadHTML($html);
libxml_clear_errors();

$xpath = new DOMXPath($dom);


//RSS Feed anlegen
if(file_exists($file_path) && $file = file_get_contents($file_path)) {
    $xml = simplexml_load_string($file);
    $channel = $xml->channel;
    $first_run = false;
} else {
    $xml = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"></rss>'); 
    $channel = $xml->addChild("channel");
    $channel->addChild("title", "Seniorenzeitung der Stadt Goslar");
    $channel->addChild("link", "https://www.goslar.de/leben-in-goslar/senioren/seniorenzeitung");
    $channel->addChild("description", "RSS Feed der Seniorenzeitung der Stadt Goslar");
    $channel->addChild("copyright", "Stadt Goslar"." ".date("Y"));
    $channel->addChild("language", "de-DE");
    $first_run = true;
}




foreach ($xpath->query('//a[contains(@href, ".pdf")]') as $link) {

    $href = $link->getAttribute('href');
    if (strpos($href, 'seniorenzeitung') !== false) {

        $full_url = "https://goslar.de".$href;
        $already_there = false;
        foreach($channel->item as $item_obj){
            
            $link_str = preg_replace('/\s+/', '', strval($item_obj->link));
            if($link_str == $full_url) {

                $already_there = true;
                break;
            }
        }


        if($already_there) break;

        if($first_run) {
            $image = $channel->addChild("image");
            $first_run = false;

        } else {
            $channel->lastBuildDate = date("Y-m-d H:i");
            $image = $channel->image;
        }

        $item = $channel->addChild("item");
        $item->link = $full_url;

        foreach($link->childNodes as $details) {
            switch ($details->className) {
                case 'image':
                    $url_path = $details->firstChild->getAttribute('src');
                    $image->url =  "https://goslar.de".$url_path;
                    $image->title = "Neuste Ausgabe";
                    $image->link = "https://www.goslar.de/leben-in-goslar/senioren/seniorenzeitung";
                    break;
                case 'description':
                    $item->addChild("description", preg_replace('/[^A-Za-z0-9\-]/', ' ', $details->textContent));
                    $item->addChild("pubDate", date("Y-m-d H:i"));
                    $item->addChild("title", "Eine neue Ausgabe der Seniorenzeitung ist erschienen!");
                    break;
                default:
                    # code...
                    break;
            }
        }
    }
}
$xml->saveXML($file_path);

?>