<?php
/*            
*                   --CONNECTS TO DB SERVER--
*       This file is important to included to all the php files.
*/

    $host = "localhost";
    $dbUsername = "root";
    $dbPassword = "admin";
    $dbName = "school";
    $conn = new mysqli($host, $dbUsername, $dbPassword, $dbName);

    if (mysqli_connect_error()) { 
        die('Connect Error(' . mysqli_connect_errno() . ')' . mysqli_connect_error());
    }
?>