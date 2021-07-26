<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Create Lesson</title>
    </head>

    <body>
        <h2>Please type the lesson you want to add</h2>
        <form action="create_new_lesson.php" method="POST">
            <table>
                <tr>
                    <td>Name:</td>
                    <td><input type="name" name="name"></td>
                    <td id="myelement">1</td>
                </tr>
                <tr>
                    <td>Description: (optional)</td>
                    <td><input type="description" name="description"></td>
                </tr>
                <tr>
                    <td>Lessons need: (optional)</td>
                    <td><input type="lesson" name="lesson"></td>
                </tr>
                <tr>
                    <td><input type="submit" value="Add" class="button"></td>
                    <td id="myelement1"></td>
                </tr>
            </table>
        </form>
    </body>
</html>

<?php

require_once "config.php";



function sql_create_lesson() {
    global $conn;

    $name=mysqli_real_escape_string($conn, $_POST['name']);
    $description=mysqli_real_escape_string($conn, $_POST['description']);
    $lesson=mysqli_real_escape_string($conn, $_POST['lesson']);

    if (empty($name)){
        return 1;
    } 

    $stmt = $conn->prepare("SELECT name FROM lessons where name=?");
    $stmt->bind_param("s", $name);
    $stmt->execute();
    $result = $stmt->get_result();
    
    function empty_description($stmt){
        $stmt = $conn->prepare("INSERT INTO lessons (name, lessons_need) VALUES (?, ?)");
        $stmt->bind_param("ss", $name, $lesson);
        $stmt->execute();
    }

    function empty_lesson($stmt){
        $stmt = $conn->prepare("INSERT INTO lessons (name, description) VALUES (?, ?)");
        $stmt->bind_param("ss", $name, $description);
        $stmt->execute();
    }

    function only_name($stmt){
        $stmt = $conn->prepare("INSERT INTO lessons (name) VALUES (?)");
        $stmt->bind_param("s", $name);
        $stmt->execute();
    }

    if($result->num_rows == 1) {
        return -1;
    } else {
        if (empty($description)) {
            empty_description($stmt);
        } else if (empty($lesson)){
            empty_lesson($stmt);
        } else {
            only_name($stmt);
        }
        
    }
}

if($_SERVER['REQUEST_METHOD'] === 'POST') {
    $sql_result = sql_create_lesson();
    if($sql_result === 1) {
        echo "<script>
        document.getElementById('myelement') = 'Name is necessary';
        </script>";
        exit();
    } else if ($sql_result === -1) {
        echo "document.getElementById('myelement1') = 'This lesson is already exists!';";
    }
}

?>

