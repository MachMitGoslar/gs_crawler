<?php 

$json = file_get_contents('https://goslar.feripro.de/api/programs/68/events');

$file = fopen("httpdocs/events.json", "w");
fwrite($file, $json);
fclose($file);

?>