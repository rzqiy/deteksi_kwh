-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Sep 11, 2025 at 09:02 AM
-- Server version: 8.0.30
-- PHP Version: 8.3.24

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `kwh_detection`
--

-- --------------------------------------------------------

--
-- Table structure for table `kwh_detection`
--

CREATE TABLE `kwh_detection` (
  `BLTH` varchar(6) NOT NULL,
  `IDPEL` varchar(20) NOT NULL,
  `KET` varchar(50) DEFAULT NULL,
  `SAHLWBP` varchar(20) DEFAULT NULL,
  `SAI` varchar(20) DEFAULT NULL,
  `ANOTASI` varchar(255) DEFAULT NULL,
  `VER` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `kwh_detection`
--

INSERT INTO `kwh_detection` (`BLTH`, `IDPEL`, `KET`, `SAHLWBP`, `SAI`, `ANOTASI`, `VER`) VALUES
('202509', '212100022680', 'kwh_jelas', '', '04958', '/static/results/88229c46-4681-4e7d-9d0e-1987b369f35b.jpg', 'sesuai'),
('202509', '212100040758', 'kwh_jelas', '', '01348', '/static/results/e59c6691-1cd7-487d-9a37-77488e4820e8.jpg', 'sesuai'),
('202509', '212100040797', 'kwh_jelas', '', '04507', '/static/results/8afc7aa3-203c-47c4-a95f-48866da1e04c.jpg', 'sesuai'),
('202509', '212100058187', 'kwh_jelas', '', '07482', '/static/results/d14a0086-bca5-4868-a184-e8c8306ae78d.jpg', 'sesuai'),
('202509', '212100102851', 'kwh_jelas', '', '03394', '/static/results/94446281-f7ae-4da2-b669-06bd6799d2f1.jpg', 'sesuai'),
('202509', '212100133803', 'kwh_jelas', '', '03442', '/static/results/be2e9d30-905e-43da-b81a-5d380ca1ea96.jpg', 'sesuai'),
('202509', '212100140072', 'kwh_jelas', '', '6826', '/static/results/2f65296b-cb12-45f3-a766-3f1677b3fc07.jpg', 'tidak'),
('202509', '212100157326', 'kwh_jelas', '', '07769', '/static/results/f128cf16-45c3-436e-bfb0-c67105696100.jpg', ''),
('202509', '212110008219', 'kwh_blur', '', '', '/static/results/ec66dc44-e890-49c9-aedb-208a3b0654e3.jpg', ''),
('202509', '212110083663', 'kwh_jelas', '', '270', '/static/results/73042912-3554-4b31-99d4-4dbbce11c1db.jpg', ''),
('202509', '212110092136', 'kwh_jelas', '', '9944', '/static/results/db505d9b-197f-4c20-8bb1-fbc56fc7b9d5.jpg', ''),
('202509', '212120035531', 'kwh_jelas', '', '06913', '/static/results/6767c6b4-d637-44e8-9d78-dcdd038b12c5.jpg', '');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `kwh_detection`
--
ALTER TABLE `kwh_detection`
  ADD PRIMARY KEY (`BLTH`,`IDPEL`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
