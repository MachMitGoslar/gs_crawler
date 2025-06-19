<?php 

$json = file_get_contents('https://goslar.feripro.de/api/programs/68/events');

$file = fopen("./output/002_fepa_events.json", "w");
fwrite($file, $json);
fclose($file);

?>