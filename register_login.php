<?php
    function checkAndRegister() {
        $conn = mysqli_connect("localhost", "root", "", "speedtest");
        $query = "SELECT `email` FROM `users` WHERE email='".$_POST["email"]."' AND username='".$_POST["username"]."' AND password='".$_POST["password"]."'";
        $count = mysqli_num_rows(mysqli_query($conn, $query));

        //checking if user already exits, then send back;
        if($count > 0) {
            mysqli_close($conn);
            echo "<script>alert('user already exits. Please login instead')</script>";
            echo "<script>history.back()</script>";
        } else {
            $query = "INSERT INTO `users` (`username`, `password`, `email`) VALUES ('".$_POST["username"]."', '".$_POST["password"]."', '".$_POST["email"]."')";
            mysqli_query($conn, $query);
            $query = "SELECT `id` FROM `users` WHERE email='".$_POST["email"]."' AND username='".$_POST["username"]."' AND password='".$_POST["password"]."'";
            $query = mysqli_fetch_array(mysqli_query($conn, $query))['id'];
            mysqli_close($conn);
            echo "<script>window.location.replace('./main.php?id=".$query."');</script>";
        }
    }

    function checkAndLogin() {
        $conn = mysqli_connect("localhost", "root", "", "speedtest");        
        $query = "SELECT `email` FROM `users` WHERE email='".$_POST["email"]."' AND username='".$_POST["username"]."' AND password='".$_POST["password"]."'";
        $count = mysqli_num_rows(mysqli_query($conn, $query));

        if($count == 0) {
            mysqli_close($conn);
            echo "<script>alert('Wrong Credentials!!')</script>";
            echo "<script>history.back()</script>";
        } else {
            $query = "SELECT `id` FROM `users` WHERE email='".$_POST["email"]."' AND username='".$_POST["username"]."' AND password='".$_POST["password"]."'";
            $query = mysqli_fetch_array(mysqli_query($conn, $query))["id"];
            mysqli_close($conn);
            echo "<script>window.location.replace('./main.php?id=".$query."');</script>";
        }
    }

    if(isset($_POST['register'])) {
        checkAndRegister();
    } else if(isset($_POST['sign-in'])) {
        checkAndLogin();
    }
?>
