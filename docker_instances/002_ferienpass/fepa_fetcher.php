<?php 

$programm_id = "68";
$output_path = "./output/";
$file_name = "002_fepa_events.json";

$file_path = $output_path.$file_name;
mkdir($output_path, 0755, true);


$json = file_get_contents('https://goslar.feripro.de/api/programs/'.$programm_id.'/events');



$file = fopen($file_path, "w");
if(fwrite($file, $json)) {
    $now = date_format(new DateTime(), "Y-m-d H:i");
    print($now." - ✅  Einträge aus Programm mit ID: ".$programm_id." gespeichert.");
}
else {
    print($now." - ❌ Programm nicht gefunden");
}
fclose($file);

?>