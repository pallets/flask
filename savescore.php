<?php
    $conn = mysqli_connect("localhost", "root", "", "speedtest");
    $uid = $_GET['uid'];
    $score = $_GET['score'];
    $query = "SELECT * FROM `bestscores` WHERE `userid`=".$uid;
    $query = mysqli_query($conn, $query);    
    if (mysqli_num_rows($query) > 0) {
        if (mysqli_fetch_array($query)['scores'] < $score ) {
            $query = "UPDATE `bestscores` SET `scores`=".$score." WHERE `userid`=".$uid;
            mysqli_query($conn, $query);
        }
    } else {
            $query = "INSERT INTO `bestscores` (`userid`, `scores`) VALUES (".$uid.", ".$score.")";
            mysqli_query($conn, $query);
    }
    echo "<script>
            window.location.replace('./main.php?id=".$uid."');
        </script>";
    mysqli_close($conn);
?>