-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 04, 2023 at 08:47 PM
-- Server version: 10.4.27-MariaDB
-- PHP Version: 8.0.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `speedtest`
--

-- --------------------------------------------------------

--
-- Table structure for table `bestscores`
--

CREATE TABLE `bestscores` (
  `id` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `scores` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bestscores`
--

INSERT INTO `bestscores` (`id`, `userid`, `scores`) VALUES
(3, 33, 42),
(4, 32, 50);

-- --------------------------------------------------------

--
-- Table structure for table `subscribe`
--

CREATE TABLE `subscribe` (
  `uid` int(10) NOT NULL,
  `email` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `subscribe`
--

INSERT INTO `subscribe` (`uid`, `email`) VALUES
(33, 'ujjwal@gmail.com');

-- --------------------------------------------------------

--
-- Table structure for table `typerdata`
--

CREATE TABLE `typerdata` (
  `id` int(11) NOT NULL,
  `data` varchar(1000) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `typerdata`
--

INSERT INTO `typerdata` (`id`, `data`) VALUES
(1, 'Once, there was a boy who became bored when he watched over the village sheep grazing on the hillside. To entertain himself, he sang out, \"Wolf! Wolf! The wolf is chasing the sheep!\" When the villagers heard the cry, they came running up the hill to drive the wolf away. But, when they arrived, they saw no wolf. The boy was amused when seeing their angry faces. \"Don\'t scream wolf, boy,\" warned the villagers, \"when there is no wolf!\" They angrily went back down the hill. Later, the shepherd boy cried out once again, \"Wolf! Wolf! The wolf is chasing the sheep!\" To his amusement, he looked on as the villagers came running up the hill to scare the wolf away. As they saw there was no wolf, they said strictly, \"Save your frightened cry for when there really is a wolf! Don\'t cry ‘wolf\' when there is no wolf!\" But the boy grinned at their words while they walked grumbling down the hill once more. Later, the boy saw a real wolf sneaking around his flock. Alarmed, he jumped on his feet and cried'),
(2, 'There once was a king named Midas who did a good deed for a Satyr. And he was then granted a wish by Dionysus, the god of wine. For his wish,Midas asked that whatever he touched would turn to gold. Despite Dionysus\' efforts to prevent it, Midas pleaded that this was a fantastic wish, and so, it was bestowed. Excited about his newly-earned powers, Midas started touching all kinds of things, turning each item into pure gold. But soon, Midas became hungry. As he picked up a piece of food, he found he couldn\'t eat it. It had turned to gold in his hand. Hungry, Midas groaned, \"I\'ll starve! Perhaps this was not such an excellent wish after all!\" Seeing his dismay, Midas\' beloved daughter threw her arms around him to comfort him, and she, too, turned to gold. \"The golden touch is no blessing,\" Midas cried.'),
(3, 'One day, a fox became very hungry as he went to search for some food. He searched high and low, but couldn\'t find something that he could eat. Finally, as his stomach rumbled, he stumbled upon a farmer\'s wall. At the top of the wall, he saw the biggest, juiciest grapes he\'d ever seen. They had a rich, purple color, telling the fox they were ready to be eaten. To reach the grapes, the fox had to jump high in the air. As he jumped, he opened his mouth to catch the grapes, but he missed. The fox tried again but missed yet again. He tried a few more times but kept failing. Finally, the fox decided it was time to give up and go home. While he walked away, he muttered, \"I\'m sure the grapes were sour anyway\"');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(30) NOT NULL,
  `password` varchar(30) NOT NULL,
  `email` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `email`) VALUES
(32, 'arcon', '12345', 'arcon@gmail.com'),
(33, 'Ujjwal', '12345', 'ujjwal@gmail.com');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bestscores`
--
ALTER TABLE `bestscores`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `typerdata`
--
ALTER TABLE `typerdata`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bestscores`
--
ALTER TABLE `bestscores`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `typerdata`
--
ALTER TABLE `typerdata`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
