<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Speed-Test</title>
        <script src="./script.js"></script>
        <link rel="stylesheet" type="text/css" href="./style.css"/>
    </head>
    <body style="background-color:powderblue;">
        <center><h1 style="color: black;font-size: 50px;margin-bottom: -10px;">TYPING TEST</h1></center>
        <hr style="margin-bottom: 0px;"/>
        <hr style="margin-bottom: 0px;"/>
        <hr/>
        <br/>
        <?php
            $conn = mysqli_connect("localhost", "root", "", "speedtest");
            $query = "SELECT * FROM `users` WHERE id='".$_GET['id']."'";
            $query = mysqli_fetch_array(mysqli_query($conn, $query));
            $USERNAME = $query["username"];
            echo "<script>userid=".$_GET['id']."</script>";
        ?>
        <div style="text-align: right; margin-bottom: -20px; margin-right: 2%;font-size: 15px;color: blue;">
            <?php echo "<strong>UserName : ".$USERNAME."</strong>" ?>
            <?php echo "<h4 onclick='logout()' style='color:red;cursor:grab'>logout</h4>" ?>
        </div>
        <div style="margin-top:5%">
            <div style="background-color: powderblue;color: black;">
                <center>
                    <h2 style="font-size: 50px;"><b id="main-text-first" style="color: brown"></b><b id="main-text-second">Click on 'START' to start test</b></h2>
                    <?php
                        $conn = mysqli_connect("localhost", "root", "", "speedtest");
                        $query = "SELECT `data` FROM `typerdata`";
                        $query = mysqli_query($conn, $query);
                        $checkdata = "";
                        echo "<script>";
                        while($temp = mysqli_fetch_array($query)) {
                            $temp = str_replace("\"","\\\"", $temp['data']);
                            echo 'wholeData.push("'.$temp.'");';
                            $checkdata = $temp;
                        }
                        echo "
                            dataCount = parseInt(Math.random()*10) % wholeData.length;
                            data = wholeData[dataCount % wholeData.length].split(\" \");
                            if (true) {
                                tempData = [];
                                for (let i = 0 ; i < 22/*data.length*/ ; i++) {
                                    if (data[i].trim().length != 0){
                                        tempData.push(data[i]);
                                    }
                                }
                                tempData.push(\" \");
                                tempData.push(\" \");
                                data = tempData;
                            }
                        </script>";
                    ?>
                </center>
            </div>

            <div>
                <center>
                    <strong>( YOUR TYPING SPEED IS : </strong><strong  id="speed_info">0</strong><strong> words/min)</strong>
                </center>
            </div><br/>
            <br/>

            <div>
                <center><input id="text-test" type="text" size="60" style="color:brown; font-weight: bold; height: 50px; text-align: center; font-size: large;margin-top: -30px;" placeholder="start typing here..." disabled></center>
                <script>
                        document.getElementById("text-test").value = "";
                        document.getElementById("text-test").disabled = true;
                </script>
            </div><br/>

            <center>
                <b>LISTEN AND TYPE</b>&nbsp
                <label class="switch">
                    <input id="listenAndtype_id" type="checkbox">
                    <span class="slider round"></span>
                </label>
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp

                <b>IGNORE CASE</b>
                &nbsp
                <label class="switch">
                    <input id="ignoreCase_id" type="checkbox">
                    <span class="slider round"></span>
                </label>
            </center><br/>

            <div>
                <center>
                    <strong style="color:blue" id="suggestion"></strong>
                </center>
            </div><br/>

            <center>
                <button style="font-size: 20px; border-radius: 20%;background-color: green;border-color: green; width: 100px;
                display: inline-block;" onclick="start()" id="start-button">Start</button>
                <button style="font-size: 20px; margin-left: 20px; border-radius: 20%; background-color: red;border-color: red; width: 100px;
                display: inline-block;" onclick='stop()'>Stop</button>
            </center>
            <br/>
            <br/>

            <center>
                <input type="checkbox" id="subscribe" onchange="showAlertForSubscribe()">
                <label for="vehicle1"><b>Subscribe to get latest-updates on your e-mail.</b></label><br>
                <?php
                    $conn = mysqli_connect("localhost", "root", "", "speedtest");
                    $query = "SELECT * FROM `subscribe` WHERE `uid`=".$_GET['id'];
                    $query = mysqli_query($conn, $query);
                    if (mysqli_num_rows($query) > 0) {
                        echo "<script>document.getElementById('subscribe').checked=true;</script>";
                    } else {
                        echo "<script>document.getElementById('subscribe').checked=false;</script>";
                    }
                ?>
            </center>

            <center>
                <h3 style="margin-bottom: 5px;margin-top: 5px;"><u>Best Scores</u></h3>
                <table id="user_info">
                    <?php
                        $conn = mysqli_connect("localhost", "root", "", "speedtest");
                        $query = "SELECT * FROM `bestscores` ORDER BY `scores` DESC";
                        $query = mysqli_query($conn, $query);
                        if (mysqli_num_rows($query) == 0) {
                            echo "null";
                        } else {
                            $i = 0;
                            while($temp = mysqli_fetch_array($query)) {
                                if($i == 5){
                                    break;
                                }
                                $i = $i + 1;
                                $USERNAME = mysqli_fetch_array(mysqli_query($conn, "SELECT `username` from `users` WHERE `id`=".$temp['userid']))['username'];
                                echo "<tr><td>".$USERNAME." </td><td>:</td><td> ".$temp['scores']." words/min</td></tr>";
                            }
                        }
                    ?>
                </table>
            </center>
        </div>
    </body>
</html>
