<?php
    $conn = mysqli_connect("localhost", "root", "", "speedtest");
    $subscribe = $_GET['subs'];
    $uid = $_GET['uid'];
    if ($subscribe == 1) {
        $query = "SELECT `email` from `users` WHERE `id`=".$uid;
        $query = "INSERT INTO `subscribe` (`uid`, `email`) VALUES (".$uid.", '".mysqli_fetch_array(mysqli_query($conn, $query))['email']."')";
        mysqli_query($conn, $query);
        echo "<script>
                alert('Subscribed successfully to get latest-updates.');
                window.location.replace('./main.php?id=".$uid."');
            </script>";
    } else {
        $query = "DELETE FROM `subscribe` WHERE `uid`=".$uid;
        mysqli_query($conn, $query);
        echo "<script>
                alert('Unsubscribed successfully!');
                window.location.replace('./main.php?id=".$uid."');
            </script>";
    }
    mysqli_close($conn);
?>
