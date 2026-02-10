CREATE DATABASE  IF NOT EXISTS `aitime` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `aitime`;
-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: aitime
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ados`
--

DROP TABLE IF EXISTS `ados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ados` (
  `a2` int DEFAULT NULL,
  `a3` int DEFAULT NULL,
  `a7` int DEFAULT NULL,
  `a8` int DEFAULT NULL,
  `b1` int DEFAULT NULL,
  `b12` int DEFAULT NULL,
  `b13` int DEFAULT NULL,
  `b14` int DEFAULT NULL,
  `b15` int DEFAULT NULL,
  `b16b` int DEFAULT NULL,
  `b18` int DEFAULT NULL,
  `b4` int DEFAULT NULL,
  `b5` int DEFAULT NULL,
  `b6` int DEFAULT NULL,
  `b7` int DEFAULT NULL,
  `b8` int DEFAULT NULL,
  `b9` int DEFAULT NULL,
  `d1` int DEFAULT NULL,
  `d2` int DEFAULT NULL,
  `d5` int DEFAULT NULL,
  `rrb_total` int DEFAULT NULL,
  `social_affect_total` int DEFAULT NULL,
  `total` int DEFAULT NULL,
  `ados_id` binary(16) NOT NULL,
  `exam_id` binary(16) NOT NULL,
  PRIMARY KEY (`ados_id`),
  KEY `fk_ados_exam` (`exam_id`),
  CONSTRAINT `fk_ados_exam` FOREIGN KEY (`exam_id`) REFERENCES `exam` (`exam_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ados`
--

LOCK TABLES `ados` WRITE;
/*!40000 ALTER TABLE `ados` DISABLE KEYS */;
INSERT INTO `ados` VALUES (NULL,1,NULL,0,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,1,2,3,_binary 'ô,d˚Ù\‘G°æ\√èÆ∫\Í9',_binary 'öññwñ.BèÉ\"{N\‡¨');
/*!40000 ALTER TABLE `ados` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `child`
--

DROP TABLE IF EXISTS `child`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `child` (
  `birthdate` date NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL,
  `child_id` binary(16) NOT NULL,
  `user_id` binary(16) NOT NULL,
  `name` varchar(50) NOT NULL,
  `gender` enum('FEMALE','MALE') NOT NULL,
  `record_status` enum('ACTIVE','DELETED') NOT NULL,
  PRIMARY KEY (`child_id`),
  KEY `idx_child_user_id` (`user_id`),
  CONSTRAINT `fk_child_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `child`
--

LOCK TABLES `child` WRITE;
/*!40000 ALTER TABLE `child` DISABLE KEYS */;
INSERT INTO `child` VALUES ('2026-01-01','2026-02-05 21:11:37.323211',NULL,'2026-02-05 21:11:37.323211',_binary '≥’ñh¿Iœâ3gn\»',_binary 'C≠≥\Ó{èO\rªﬂ≥vˇ\‹¿','ÍπÄÏ≤†Ïàò','MALE','ACTIVE'),('2024-02-06','2026-02-06 13:44:58.849320','2026-02-06 13:45:09.000000','2026-02-06 13:44:58.849320',_binary '¸ªM_J˝ºΩR‡®øè\‘',_binary 'á/\Î@\‡á¢º6:1~£','Î∞ïÎèôÌïú','MALE','DELETED'),('2024-08-05','2026-02-05 12:40:47.699044',NULL,'2026-02-05 12:40:47.699044',_binary '$∫àW\”\–Aè¥Û?˘®~ı',_binary 'MáøÃîFá\«F\≈\◊]','ÌÖåÏä§Ìä∏ÏïÑÏù¥','MALE','ACTIVE'),('2024-05-30','2026-02-06 16:18:45.907131',NULL,'2026-02-06 16:18:45.907131',_binary '3\·™¡¸tE/ºˇåºxï\‰',_binary 'ú\◊\ W\ÈyNZà{ı¸\"M\·¯','Î∞ïÎèôÌïú','MALE','ACTIVE'),('2024-01-01','2026-02-06 12:51:02.297349',NULL,'2026-02-06 12:51:02.297349',_binary 'uÑ+\Â^Dp†π¿Øç_\ÿ',_binary 'á/\Î@\‡á¢º6:1~£','ÍπÄÌö®ÏÑù','MALE','ACTIVE'),('2025-01-01','2026-02-05 21:12:01.593512',NULL,'2026-02-05 21:12:01.593512',_binary 'ïOÈ≤¥¯Jíán˛zKì',_binary 'C≠≥\Ó{èO\rªﬂ≥vˇ\‹¿','ÍπÄÏßÑÏàò','FEMALE','ACTIVE'),('2025-08-08','2026-02-05 21:12:23.300584',NULL,'2026-02-05 21:12:23.300584',_binary 'ñ\È¿\€\›OFò\‘¥î¨ &',_binary 'C≠≥\Ó{èO\rªﬂ≥vˇ\‹¿','ÍπÄÍ∞êÏàò','MALE','ACTIVE'),('2024-05-30','2026-02-05 21:41:01.468048',NULL,'2026-02-05 21:41:01.468048',_binary '\÷tuè{@Ñ\È	EA∑¢4',_binary 'á/\Î@\‡á¢º6:1~£','Ïò§ÏßÄÏàò','FEMALE','ACTIVE'),('2024-05-30','2026-02-06 13:45:23.064762',NULL,'2026-02-06 13:45:23.064762',_binary '\Ï∏R∏ã\„OX±eL\—]˙K^',_binary 'á/\Î@\‡á¢º6:1~£','Î∞ïÎèôÌïú','MALE','ACTIVE'),('2024-08-05','2026-02-05 12:41:46.411016',NULL,'2026-02-05 12:41:46.411016',_binary '\Ôlø.\‹\œBõºòˇ`\«`∏ö',_binary 'ú\◊\ W\ÈyNZà{ı¸\"M\·¯','ÌÖåÏä§Ìä∏ÏïÑÏù¥','MALE','ACTIVE');
/*!40000 ALTER TABLE `child` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exam`
--

DROP TABLE IF EXISTS `exam`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam` (
  `is_submitted` bit(1) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `draft_expires_at` datetime(6) DEFAULT NULL,
  `exam_started_at` datetime(6) DEFAULT NULL,
  `next_eligible_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL,
  `child_id` binary(16) NOT NULL,
  `exam_id` binary(16) NOT NULL,
  `exam_status` enum('COMPLETED','IN_PROGRESS') NOT NULL,
  PRIMARY KEY (`exam_id`),
  KEY `fk_exam_child` (`child_id`),
  CONSTRAINT `fk_exam_child` FOREIGN KEY (`child_id`) REFERENCES `child` (`child_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exam`
--

LOCK TABLES `exam` WRITE;
/*!40000 ALTER TABLE `exam` DISABLE KEYS */;
INSERT INTO `exam` VALUES (_binary '\0',NULL,'2026-02-06 16:19:47.671577',NULL,'2026-02-09 16:19:47.671067',NULL,NULL,'2026-02-06 16:19:47.671577',_binary '3\·™¡¸tE/ºˇåºxï\‰',_binary 'YÆ\‰\‘$A[ñ\\ä\"\n\0e','IN_PROGRESS'),(_binary '\0',NULL,'2026-02-06 12:52:16.256111',NULL,'2026-02-09 12:52:16.256111',NULL,NULL,'2026-02-06 12:52:16.256111',_binary 'uÑ+\Â^Dp†π¿Øç_\ÿ',_binary '+≤A\»¯ΩL∆µH\∆\—\‰˚\”','IN_PROGRESS'),(_binary '\0',NULL,'2026-02-05 12:40:47.700050',NULL,NULL,NULL,NULL,'2026-02-05 12:40:47.700050',_binary '$∫àW\”\–Aè¥Û?˘®~ı',_binary 'S=ItPO≤,\÷\÷D\ﬂ\‡','IN_PROGRESS'),(_binary '','2026-02-06 14:23:54.554127','2026-02-05 12:41:46.412015',NULL,NULL,NULL,'2026-05-05 12:41:46.413527','2026-02-06 14:23:54.558126',_binary '\Ôlø.\‹\œBõºòˇ`\«`∏ö',_binary 'öññwñ.BèÉ\"{N\‡¨','COMPLETED'),(_binary '\0',NULL,'2026-02-06 13:46:14.067327',NULL,'2026-02-09 13:46:14.066808',NULL,NULL,'2026-02-06 13:46:14.067327',_binary '\Ï∏R∏ã\„OX±eL\—]˙K^',_binary '´ñî—∏G◊òΩnö˚\ƒw\ﬂ','IN_PROGRESS'),(_binary '\0',NULL,'2026-02-06 12:41:10.040842',NULL,'2026-02-09 12:41:10.031272',NULL,NULL,'2026-02-06 12:41:10.040842',_binary '\÷tuè{@Ñ\È	EA∑¢4',_binary 'øÆ∫òOETñ\Ã\–\Ìv˛7\Ã','IN_PROGRESS');
/*!40000 ALTER TABLE `exam` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hospital`
--

DROP TABLE IF EXISTS `hospital`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hospital` (
  `created_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL,
  `hospital_id` binary(16) NOT NULL,
  `phone_number` varchar(20) NOT NULL,
  `hospital_code` varchar(100) NOT NULL,
  `name` varchar(100) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `record_status` enum('ACTIVE','DELETED') NOT NULL,
  PRIMARY KEY (`hospital_id`),
  UNIQUE KEY `uk_hospital_code` (`hospital_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hospital`
--

LOCK TABLES `hospital` WRITE;
/*!40000 ALTER TABLE `hospital` DISABLE KEYS */;
INSERT INTO `hospital` VALUES ('2026-02-05 12:40:00.990585',NULL,'2026-02-05 12:40:00.990585',_binary '=(Ü\ƒ2oMéäœüó\≈ú','02-123-4562','H002','Ï†ú2 ÏïÑÏù¥Îã§ÏûÑ ÏÜåÏïÑÍ≥º','ÏÑúÏö∏Ïãú Í∞ïÎÇ®Íµ¨ ÌÖåÌó§ÎûÄÎ°ú 2Í∏∏','ACTIVE'),('2026-02-05 12:40:00.963747',NULL,'2026-02-05 12:40:00.963747',_binary 'ªú{=qJ\ZåÛë¢\'sÆ','02-123-4561','H001','Ï†ú1 ÏïÑÏù¥Îã§ÏûÑ ÏÜåÏïÑÍ≥º','ÏÑúÏö∏Ïãú Í∞ïÎÇ®Íµ¨ ÌÖåÌó§ÎûÄÎ°ú 1Í∏∏','ACTIVE');
/*!40000 ALTER TABLE `hospital` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hospital_children`
--

DROP TABLE IF EXISTS `hospital_children`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hospital_children` (
  `deleted_at` datetime(6) DEFAULT NULL,
  `registered_at` datetime(6) NOT NULL,
  `children_id` binary(16) NOT NULL,
  `hospital_children_id` binary(16) NOT NULL,
  `hospital_id` binary(16) NOT NULL,
  `link_status` enum('ACTIVE','INACTIVE') NOT NULL,
  PRIMARY KEY (`hospital_children_id`),
  UNIQUE KEY `uk_hospital_children` (`children_id`,`hospital_id`),
  KEY `fk_hospital_children_hospital` (`hospital_id`),
  CONSTRAINT `fk_hospital_children_child` FOREIGN KEY (`children_id`) REFERENCES `child` (`child_id`),
  CONSTRAINT `fk_hospital_children_hospital` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hospital_children`
--

LOCK TABLES `hospital_children` WRITE;
/*!40000 ALTER TABLE `hospital_children` DISABLE KEYS */;
INSERT INTO `hospital_children` VALUES (NULL,'2026-02-06 16:19:44.202620',_binary '3\·™¡¸tE/ºˇåºxï\‰',_binary '5¯N\"J;öC Ü\0°Å\…',_binary 'ªú{=qJ\ZåÛë¢\'sÆ','ACTIVE'),(NULL,'2026-02-05 21:48:20.279161',_binary '\÷tuè{@Ñ\È	EA∑¢4',_binary '\r$}èÙMê´\\E‚ÆÇ\\\ﬁ',_binary 'ªú{=qJ\ZåÛë¢\'sÆ','ACTIVE'),(NULL,'2026-02-06 13:46:10.358712',_binary '\Ï∏R∏ã\„OX±eL\—]˙K^',_binary '¶¡\ÍGÇ°\Á{˚ø≤j',_binary 'ªú{=qJ\ZåÛë¢\'sÆ','ACTIVE'),(NULL,'2026-02-06 12:52:12.767041',_binary 'uÑ+\Â^Dp†π¿Øç_\ÿ',_binary '%\“j¥®ÑLó£∏í±8#\Î˚',_binary 'ªú{=qJ\ZåÛë¢\'sÆ','ACTIVE'),(NULL,'2026-02-05 12:47:03.810624',_binary '\Ôlø.\‹\œBõºòˇ`\«`∏ö',_binary '€ù0jôHH#ë{\ƒ~\'zjD',_binary '=(Ü\ƒ2oMéäœüó\≈ú','ACTIVE');
/*!40000 ALTER TABLE `hospital_children` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hospital_staff`
--

DROP TABLE IF EXISTS `hospital_staff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hospital_staff` (
  `created_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL,
  `hospital_id` binary(16) NOT NULL,
  `hospital_staff_id` binary(16) NOT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `name` varchar(50) NOT NULL,
  `login_id` varchar(100) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `record_status` enum('ACTIVE','DELETED') NOT NULL,
  `staff_role` enum('DESK','DOCTOR') NOT NULL,
  PRIMARY KEY (`hospital_staff_id`),
  UNIQUE KEY `uk_hospital_staff_login_id` (`login_id`),
  KEY `idx_hospital_staff_hospital_id` (`hospital_id`),
  CONSTRAINT `fk_hospital_staff_hospital` FOREIGN KEY (`hospital_id`) REFERENCES `hospital` (`hospital_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hospital_staff`
--

LOCK TABLES `hospital_staff` WRITE;
/*!40000 ALTER TABLE `hospital_staff` DISABLE KEYS */;
INSERT INTO `hospital_staff` VALUES ('2026-02-05 12:40:00.991585',NULL,'2026-02-05 12:40:00.991585',_binary '=(Ü\ƒ2oMéäœüó\≈ú',_binary '#sπfO◊ßj\n%\ƒ[0\Á',NULL,'ÏùòÏÇ¨3','doctor3',NULL,'$2a$10$yLvbhrdCG4IX02iqGPxa1.bwUgSYK7JKf3JA0syD5Rdx3.yPST9pm','ACTIVE','DOCTOR'),('2026-02-05 12:40:00.989067',NULL,'2026-02-05 12:40:00.989067',_binary 'ªú{=qJ\ZåÛë¢\'sÆ',_binary 'v=P¸CN‘Ñ\‰ÏößGl>',NULL,'Îç∞Ïä§ÌÅ¨1','desk1',NULL,'$2a$10$yLvbhrdCG4IX02iqGPxa1.bwUgSYK7JKf3JA0syD5Rdx3.yPST9pm','ACTIVE','DESK'),('2026-02-05 12:40:00.989576',NULL,'2026-02-05 12:40:00.989576',_binary 'ªú{=qJ\ZåÛë¢\'sÆ',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',NULL,'ÏùòÏÇ¨1','doctor1',NULL,'$2a$10$yLvbhrdCG4IX02iqGPxa1.bwUgSYK7JKf3JA0syD5Rdx3.yPST9pm','ACTIVE','DOCTOR'),('2026-02-05 12:40:00.991585',NULL,'2026-02-05 12:40:00.991585',_binary '=(Ü\ƒ2oMéäœüó\≈ú',_binary 'ßüï∏\ƒ\“B≤ßo4˛[yt',NULL,'ÏùòÏÇ¨4','doctor4',NULL,'$2a$10$yLvbhrdCG4IX02iqGPxa1.bwUgSYK7JKf3JA0syD5Rdx3.yPST9pm','ACTIVE','DOCTOR'),('2026-02-05 12:40:00.990585',NULL,'2026-02-05 12:40:00.990585',_binary '=(Ü\ƒ2oMéäœüó\≈ú',_binary '\Ï\≈‹àë\«K<ì&˚\ÓbíK_',NULL,'Îç∞Ïä§ÌÅ¨2','desk2',NULL,'$2a$10$yLvbhrdCG4IX02iqGPxa1.bwUgSYK7JKf3JA0syD5Rdx3.yPST9pm','ACTIVE','DESK'),('2026-02-05 12:40:00.990585',NULL,'2026-02-05 12:40:00.990585',_binary 'ªú{=qJ\ZåÛë¢\'sÆ',_binary '¸è\Ó	\—IVå[åŒûâ\'',NULL,'ÏùòÏÇ¨2','doctor2',NULL,'$2a$10$yLvbhrdCG4IX02iqGPxa1.bwUgSYK7JKf3JA0syD5Rdx3.yPST9pm','ACTIVE','DOCTOR');
/*!40000 ALTER TABLE `hospital_staff` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invite_code`
--

DROP TABLE IF EXISTS `invite_code`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invite_code` (
  `child_birthdate` date NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `scheduled_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `doctor_id` binary(16) DEFAULT NULL,
  `hospital_staff_id` binary(16) NOT NULL,
  `invite_code_id` binary(16) NOT NULL,
  `invite_code` varchar(20) NOT NULL,
  `parent_phone` varchar(20) NOT NULL,
  `child_name` varchar(50) NOT NULL,
  `invite_code_status` enum('ISSUED','REGISTERED','REVOKED') NOT NULL,
  PRIMARY KEY (`invite_code_id`),
  UNIQUE KEY `uk_invite_code_value` (`invite_code`),
  KEY `fk_invite_code_staff` (`hospital_staff_id`),
  CONSTRAINT `fk_invite_code_staff` FOREIGN KEY (`hospital_staff_id`) REFERENCES `hospital_staff` (`hospital_staff_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invite_code`
--

LOCK TABLES `invite_code` WRITE;
/*!40000 ALTER TABLE `invite_code` DISABLE KEYS */;
INSERT INTO `invite_code` VALUES ('2024-05-30','2026-02-06 13:46:05.687896',NULL,'2026-02-05 19:45:00.000000','2026-02-06 13:46:10.359712',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',_binary 'v=P¸CN‘Ñ\‰ÏößGl>',_binary '˘%Ù\‰≤F ¢b\›•S/','FTL-HGLR-88','01044007413','Î∞ïÎèôÌïú','REGISTERED'),('2024-05-30','2026-02-06 16:19:38.563603',NULL,'2026-02-05 22:19:00.000000','2026-02-06 16:19:44.206151',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',_binary 'v=P¸CN‘Ñ\‰ÏößGl>',_binary '+\ÿK.ÛRKñås	wÚt,g','FTL-TIVW-05','01052015497','Î∞ïÎèôÌïú','REGISTERED'),('2024-05-30','2026-02-05 21:48:14.842756',NULL,'2026-02-26 03:48:00.000000','2026-02-05 21:48:20.296522',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',_binary 'v=P¸CN‘Ñ\‰ÏößGl>',_binary 'õúØœ∏ÉC¸±˝+•y\€c','FTL-FGWC-37','01044007413','Ïò§ÏßÄÏàò','REGISTERED'),('2024-01-01','2026-02-06 12:52:03.101048',NULL,'2026-02-05 18:51:00.000000','2026-02-06 12:52:12.773564',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',_binary 'v=P¸CN‘Ñ\‰ÏößGl>',_binary 'ºaõ4\ﬁJGj∞\ ˛ùKf\Ã\Ï','FTL-CIW9-34','01044007413','ÍπÄÌö®ÏÑù','REGISTERED'),('2024-08-05','2026-02-05 12:44:56.470670',NULL,'2026-03-01 14:00:00.000000','2026-02-05 12:47:03.819815',_binary 'ßüï∏\ƒ\“B≤ßo4˛[yt',_binary '\Ï\≈‹àë\«K<ì&˚\ÓbíK_',_binary '…≠@\Ï∂\ZCHö∑Ih<#\Z','FTL-I85Z-55','01052015497','ÌÖåÏä§Ìä∏ÏïÑÏù¥','REGISTERED');
/*!40000 ALTER TABLE `invite_code` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `name_facing_event`
--

DROP TABLE IF EXISTS `name_facing_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `name_facing_event` (
  `gaze_duration_s` double DEFAULT NULL,
  `latency_s` double DEFAULT NULL,
  `success` bit(1) DEFAULT NULL,
  `trial_end_s` double DEFAULT NULL,
  `trial_index` int NOT NULL,
  `trial_start_s` double DEFAULT NULL,
  `name_facing_event_id` binary(16) NOT NULL,
  `name_facing_trial_id` binary(16) NOT NULL,
  `emotion` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`name_facing_event_id`),
  KEY `fk_name_facing_event_trial` (`name_facing_trial_id`),
  CONSTRAINT `fk_name_facing_event_trial` FOREIGN KEY (`name_facing_trial_id`) REFERENCES `name_facing_trial` (`name_facing_trial_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `name_facing_event`
--

LOCK TABLES `name_facing_event` WRITE;
/*!40000 ALTER TABLE `name_facing_event` DISABLE KEYS */;
INSERT INTO `name_facing_event` VALUES (1.8,1.2,_binary '',7.2,2,4,_binary 'ù\‡Aê0NÃ≤∫ñ\Îº∆∫',_binary 'ë\À{wEI⁄Å3s¢ßn∏','neutral'),(2.5,0.8,_binary '',3.5,1,0,_binary '\¬lg5[µ@Ãæ+~¶ùÆW4',_binary 'ë\À{wEI⁄Å3s¢ßn∏','smile'),(0,NULL,_binary '\0',11.5,3,8,_binary '\ﬁ(.\ÂI]Eû8\Âû\·\–o',_binary 'ë\À{wEI⁄Å3s¢ßn∏','neutral');
/*!40000 ALTER TABLE `name_facing_event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `name_facing_trial`
--

DROP TABLE IF EXISTS `name_facing_trial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `name_facing_trial` (
  `name_facing_trial_id` binary(16) NOT NULL,
  `video_id` binary(16) NOT NULL,
  `ados_b1` varchar(50) DEFAULT NULL,
  `ados_b18` varchar(50) DEFAULT NULL,
  `ados_b4` varchar(50) DEFAULT NULL,
  `ados_b6` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`name_facing_trial_id`),
  KEY `fk_name_facing_video` (`video_id`),
  CONSTRAINT `fk_name_facing_video` FOREIGN KEY (`video_id`) REFERENCES `video` (`video_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `name_facing_trial`
--

LOCK TABLES `name_facing_trial` WRITE;
/*!40000 ALTER TABLE `name_facing_trial` DISABLE KEYS */;
INSERT INTO `name_facing_trial` VALUES (_binary 'ë\À{wEI⁄Å3s¢ßn∏',_binary 'R\¬]!( Jwè(Æ•ª~4\„','0','TRUE','1','FALSE');
/*!40000 ALTER TABLE `name_facing_trial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `name_non_facing_event`
--

DROP TABLE IF EXISTS `name_non_facing_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `name_non_facing_event` (
  `gaze_duration_s` double DEFAULT NULL,
  `gaze_match` bit(1) DEFAULT NULL,
  `head_pitch_deg` double DEFAULT NULL,
  `head_yaw_deg` double DEFAULT NULL,
  `latency_s` double DEFAULT NULL,
  `success` bit(1) DEFAULT NULL,
  `trial_index` int NOT NULL,
  `trigger_end_s` double DEFAULT NULL,
  `trigger_start_s` double DEFAULT NULL,
  `voice_confidence` double DEFAULT NULL,
  `voice_detected` bit(1) DEFAULT NULL,
  `voice_duration_s` double DEFAULT NULL,
  `voice_end_s` double DEFAULT NULL,
  `voice_start_s` double DEFAULT NULL,
  `name_non_facing_event_id` binary(16) NOT NULL,
  `name_non_facing_trial_id` binary(16) NOT NULL,
  `trigger_text` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`name_non_facing_event_id`),
  KEY `fk_name_non_facing_event_trial` (`name_non_facing_trial_id`),
  CONSTRAINT `fk_name_non_facing_event_trial` FOREIGN KEY (`name_non_facing_trial_id`) REFERENCES `name_non_facing_trial` (`name_non_facing_trial_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `name_non_facing_event`
--

LOCK TABLES `name_non_facing_event` WRITE;
/*!40000 ALTER TABLE `name_non_facing_event` DISABLE KEYS */;
INSERT INTO `name_non_facing_event` VALUES (NULL,_binary '\0',NULL,NULL,NULL,_binary '\0',3,8,7,NULL,_binary '\0',NULL,NULL,NULL,_binary '˝w\Ã˛{EÉ  µG“á§',_binary 'Ü>AEŸπ,Ù1dΩ','ÎèôÌïú'),(1.5,_binary '',-2.1,5.2,1.1,_binary '',2,4.5,3,0.82,_binary '',1.7,6.2,4.5,_binary '#∂ô\ M™õ\Ÿ	Ä\ﬂv',_binary 'Ü>AEŸπ,Ù1dΩ','ÎèôÌïúÏïÑ'),(NULL,_binary '\0',NULL,NULL,0.8,_binary '',1,1.2,0,0.75,_binary '',1.3,2.5,1.2,_binary 'ÄS\¬Ú\ÏtG£iπD≠{î\'',_binary 'Ü>AEŸπ,Ù1dΩ','ÎèôÌïú');
/*!40000 ALTER TABLE `name_non_facing_event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `name_non_facing_trial`
--

DROP TABLE IF EXISTS `name_non_facing_trial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `name_non_facing_trial` (
  `name_non_facing_trial_id` binary(16) NOT NULL,
  `video_id` binary(16) NOT NULL,
  `ados_b18` varchar(50) DEFAULT NULL,
  `ados_b7` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`name_non_facing_trial_id`),
  KEY `fk_name_non_facing_video` (`video_id`),
  CONSTRAINT `fk_name_non_facing_video` FOREIGN KEY (`video_id`) REFERENCES `video` (`video_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `name_non_facing_trial`
--

LOCK TABLES `name_non_facing_trial` WRITE;
/*!40000 ALTER TABLE `name_non_facing_trial` DISABLE KEYS */;
INSERT INTO `name_non_facing_trial` VALUES (_binary 'Ü>AEŸπ,Ù1dΩ',_binary '3ó\·_ıOn†›≤ü¬ú','FALSE','2');
/*!40000 ALTER TABLE `name_non_facing_trial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pose_imitation_event`
--

DROP TABLE IF EXISTS `pose_imitation_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pose_imitation_event` (
  `attention_ratio` double DEFAULT NULL,
  `child_end_time` double DEFAULT NULL,
  `child_start_time` double DEFAULT NULL,
  `duration_s` double DEFAULT NULL,
  `latency_s` double DEFAULT NULL,
  `parent_end_time` double DEFAULT NULL,
  `parent_start_time` double DEFAULT NULL,
  `similarity_score` double DEFAULT NULL,
  `success` bit(1) DEFAULT NULL,
  `trial_index` int NOT NULL,
  `pose_imitation_event_id` binary(16) NOT NULL,
  `pose_imitation_trial_id` binary(16) NOT NULL,
  `action_type` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`pose_imitation_event_id`),
  KEY `fk_pose_imitation_event_trial` (`pose_imitation_trial_id`),
  CONSTRAINT `fk_pose_imitation_event_trial` FOREIGN KEY (`pose_imitation_trial_id`) REFERENCES `pose_imitation_trial` (`pose_imitation_trial_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pose_imitation_event`
--

LOCK TABLES `pose_imitation_event` WRITE;
/*!40000 ALTER TABLE `pose_imitation_event` DISABLE KEYS */;
INSERT INTO `pose_imitation_event` VALUES (0.92,7.7,4.2,3.5,1.2,3,0,0.85,_binary '',1,_binary '®aMFE¿µ\ÌoQ–Étü',_binary 'R\›˝\‹^äK”ø∂ì\Á7\’r','clapping'),(0.95,15.8,12.5,3.3,1.5,11,8,0.91,_binary '',2,_binary 'ûr¿PT\‘K\\Å@w\'3j',_binary 'R\›˝\‹^äK”ø∂ì\Á7\’r','waving'),(0.7,24,22,2,1,21,18,0.45,_binary '\0',3,_binary '\·Fó,‘´E≥™(V\÷¯–å:',_binary 'R\›˝\‹^äK”ø∂ì\Á7\’r','pointing');
/*!40000 ALTER TABLE `pose_imitation_event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pose_imitation_trial`
--

DROP TABLE IF EXISTS `pose_imitation_trial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pose_imitation_trial` (
  `pose_imitation_trial_id` binary(16) NOT NULL,
  `video_id` binary(16) NOT NULL,
  `ados_a8` varchar(50) DEFAULT NULL,
  `ados_b18` varchar(50) DEFAULT NULL,
  `ados_b6` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`pose_imitation_trial_id`),
  KEY `fk_pose_imitation_video` (`video_id`),
  CONSTRAINT `fk_pose_imitation_video` FOREIGN KEY (`video_id`) REFERENCES `video` (`video_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pose_imitation_trial`
--

LOCK TABLES `pose_imitation_trial` WRITE;
/*!40000 ALTER TABLE `pose_imitation_trial` DISABLE KEYS */;
INSERT INTO `pose_imitation_trial` VALUES (_binary 'R\›˝\‹^äK”ø∂ì\Á7\’r',_binary 'c\ÊQå6IIægOÛ\Œ\'d_','0','FALSE','TRUE');
/*!40000 ALTER TABLE `pose_imitation_trial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reservation`
--

DROP TABLE IF EXISTS `reservation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reservation` (
  `cancelled_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `scheduled_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `doctor_id` binary(16) DEFAULT NULL,
  `hospital_children_id` binary(16) NOT NULL,
  `reservation_id` binary(16) NOT NULL,
  `reservation_status` enum('CANCELLED','DONE','SCHEDULED') NOT NULL,
  PRIMARY KEY (`reservation_id`),
  KEY `fk_reservation_hospital_children` (`hospital_children_id`),
  CONSTRAINT `fk_reservation_hospital_children` FOREIGN KEY (`hospital_children_id`) REFERENCES `hospital_children` (`hospital_children_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reservation`
--

LOCK TABLES `reservation` WRITE;
/*!40000 ALTER TABLE `reservation` DISABLE KEYS */;
INSERT INTO `reservation` VALUES (NULL,'2026-02-06 12:52:12.773564',NULL,'2026-02-05 18:51:00.000000','2026-02-06 12:52:12.773564',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',_binary '%\“j¥®ÑLó£∏í±8#\Î˚',_binary 'â∏ı\∆m@À≤ûm\Êmi)','SCHEDULED'),(NULL,'2026-02-06 16:19:44.206151',NULL,'2026-02-05 22:19:00.000000','2026-02-06 16:19:44.206151',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',_binary '5¯N\"J;öC Ü\0°Å\…',_binary 'ãù∞IFaí\ŸSEÉ`õ?','SCHEDULED'),(NULL,'2026-02-05 12:47:03.818813',NULL,'2026-03-01 14:00:00.000000','2026-02-05 12:47:03.818813',_binary 'ßüï∏\ƒ\“B≤ßo4˛[yt',_binary '€ù0jôHH#ë{\ƒ~\'zjD',_binary 'çƒñ@A\ÃBÇõ0ßeqwî/','SCHEDULED'),(NULL,'2026-02-06 13:46:10.359712',NULL,'2026-02-05 19:45:00.000000','2026-02-06 13:46:10.359712',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',_binary '¶¡\ÍGÇ°\Á{˚ø≤j',_binary '˙©∫≠É¥H≥∞i≠\Zü2Û','SCHEDULED'),(NULL,'2026-02-05 21:48:20.295508',NULL,'2026-02-26 03:48:00.000000','2026-02-05 21:48:20.295508',_binary 'õ)†…°ıC{§ßéÖÜ¨ÙC',_binary '\r$}èÙMê´\\E‚ÆÇ\\\ﬁ',_binary '˛|\÷béG¢ëäì◊£`\ ','SCHEDULED');
/*!40000 ALTER TABLE `reservation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `speech_imitation_event`
--

DROP TABLE IF EXISTS `speech_imitation_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `speech_imitation_event` (
  `freq_abnormal` bit(1) DEFAULT NULL,
  `latency_s` double DEFAULT NULL,
  `response_detected` bit(1) DEFAULT NULL,
  `success` bit(1) DEFAULT NULL,
  `trial_end_s` double DEFAULT NULL,
  `trial_index` int NOT NULL,
  `trial_start_s` double DEFAULT NULL,
  `speech_imitation_event_id` binary(16) NOT NULL,
  `speech_imitation_trial_id` binary(16) NOT NULL,
  `stimulus_id` varchar(50) DEFAULT NULL,
  `failure_reason` varchar(255) DEFAULT NULL,
  `stimulus_text` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`speech_imitation_event_id`),
  KEY `fk_speech_imitation_event_trial` (`speech_imitation_trial_id`),
  CONSTRAINT `fk_speech_imitation_event_trial` FOREIGN KEY (`speech_imitation_trial_id`) REFERENCES `speech_imitation_trial` (`speech_imitation_trial_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `speech_imitation_event`
--

LOCK TABLES `speech_imitation_event` WRITE;
/*!40000 ALTER TABLE `speech_imitation_event` DISABLE KEYS */;
INSERT INTO `speech_imitation_event` VALUES (_binary '',NULL,_binary '\0',_binary '\0',8.1,3,6,_binary '6•ı\"I πN0\‘\Ó]∑X',_binary 'j\ﬂX\ríÉOóèN\‡»Ä\Ÿ','VI12_03','no_response','Ïùë'),(_binary '\0',0.95,_binary '',_binary '',5.2,2,3,_binary 'n®ÙU\¬˝I˛Ø*j\ŒyΩ',_binary 'j\ﬂX\ríÉOóèN\‡»Ä\Ÿ','VI12_02',NULL,'ÏóÑÎßà'),(_binary '\0',1.12,_binary '',_binary '',2.5,1,0,_binary 'êøyı\«AKÄπ˜ägln0',_binary 'j\ﬂX\ríÉOóèN\‡»Ä\Ÿ','VI12_01',NULL,'ÏïÑ');
/*!40000 ALTER TABLE `speech_imitation_event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `speech_imitation_trial`
--

DROP TABLE IF EXISTS `speech_imitation_trial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `speech_imitation_trial` (
  `speech_imitation_trial_id` binary(16) NOT NULL,
  `video_id` binary(16) NOT NULL,
  `ados_a3` varchar(50) DEFAULT NULL,
  `ados_b18` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`speech_imitation_trial_id`),
  KEY `fk_speech_imitation_video` (`video_id`),
  CONSTRAINT `fk_speech_imitation_video` FOREIGN KEY (`video_id`) REFERENCES `video` (`video_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `speech_imitation_trial`
--

LOCK TABLES `speech_imitation_trial` WRITE;
/*!40000 ALTER TABLE `speech_imitation_trial` DISABLE KEYS */;
INSERT INTO `speech_imitation_trial` VALUES (_binary 'j\ﬂX\ríÉOóèN\‡»Ä\Ÿ',_binary 'ìu\Àn\‘G®∫Ø\È#ã6\—','1','TRUE');
/*!40000 ALTER TABLE `speech_imitation_trial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `privacy_agreed` bit(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` binary(16) NOT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `name` varchar(50) NOT NULL,
  `login_id` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `record_status` enum('ACTIVE','DELETED') NOT NULL,
  `user_role` enum('ADMIN','USER') NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uk_users_login_id` (`login_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (_binary '','2026-02-05 21:10:58.356187',NULL,'2026-02-05 21:10:58.356187',_binary 'C≠≥\Ó{èO\rªﬂ≥vˇ\‹¿','01089481438','„Ñ¥„Ñ¥','doctor1','$2a$10$UEMjXIKUF6mwFxf/Feacj.hzz.CieB4nXiO2taBm/lyJ4BDlbpED6','ACTIVE','USER'),(_binary '','2026-02-05 12:40:47.697547',NULL,'2026-02-05 12:40:47.697547',_binary 'MáøÃîFá\«F\≈\◊]','010-5201-5497','ÌÖåÏä§Ìä∏Î∂ÄÎ™®','test_1770262847628','$2a$10$ltXubBANJB60piDVpsTBbu.x35p26xG1bkxEzYg8jT1lFKLx/wspy','ACTIVE','USER'),(_binary '','2026-02-05 21:40:41.727006',NULL,'2026-02-05 21:40:41.727006',_binary 'á/\Î@\‡á¢º6:1~£','01044007413','ÍπÄÏ∞å','guest1234','$2a$10$17Rbuabo.UqhnGBaT7srfecs9Z7mkyZqgtfCnBUlGgJRNRyiu0t1O','ACTIVE','USER'),(_binary '','2026-02-05 12:41:46.410018',NULL,'2026-02-05 12:41:46.410018',_binary 'ú\◊\ W\ÈyNZà{ı¸\"M\·¯','010-5201-5497','ÌÖåÏä§Ìä∏Î∂ÄÎ™®','test_1770262906328','$2a$10$8iCmVM4xXMU.fxqbjmjXv.gKU5B9raRv0g1rOzJwaj.i/gpyWjonC','ACTIVE','USER');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `video`
--

DROP TABLE IF EXISTS `video`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `video` (
  `duration_sec` int DEFAULT NULL,
  `analysis_completed_at` datetime(6) DEFAULT NULL,
  `analysis_requested_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `recorded_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL,
  `exam_id` binary(16) NOT NULL,
  `video_id` binary(16) NOT NULL,
  `model_version` varchar(50) DEFAULT NULL,
  `s3_bucket` varchar(63) DEFAULT NULL,
  `fail_reason` text,
  `s3_key` varchar(255) NOT NULL,
  `analysis_status` enum('FAILED','PENDING','PROCESSING','SUCCESS') DEFAULT NULL,
  `video_status` enum('DELETED','DELETED_PENDING','PENDING_UPLOAD','UPLOADED') NOT NULL,
  `video_type` enum('NAME_FACING','NAME_NON_FACING','POSE_IMITATION','SPEECH_IMITATION') NOT NULL,
  PRIMARY KEY (`video_id`),
  UNIQUE KEY `uk_video_exam_type` (`exam_id`,`video_type`),
  KEY `idx_video_exam_status` (`exam_id`,`analysis_status`),
  CONSTRAINT `fk_video_exam` FOREIGN KEY (`exam_id`) REFERENCES `exam` (`exam_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `video`
--

LOCK TABLES `video` WRITE;
/*!40000 ALTER TABLE `video` DISABLE KEYS */;
INSERT INTO `video` VALUES (NULL,NULL,NULL,'2026-02-05 12:40:47.701050',NULL,'2026-02-05 12:40:47.701050','2026-02-05 12:40:47.701050',_binary 'S=ItPO≤,\÷\÷D\ﬂ\‡',_binary 't\Ëm>L\Ì•.&?\€\Ã\«',NULL,'test-bucket',NULL,'test-videos/video2.mp4',NULL,'UPLOADED','SPEECH_IMITATION'),(NULL,NULL,NULL,'2026-02-05 12:40:47.701050',NULL,'2026-02-05 12:40:47.701050','2026-02-05 12:40:47.701050',_binary 'S=ItPO≤,\÷\÷D\ﬂ\‡',_binary '%á<\nS.Fßü^\r\n˛˝u',NULL,'test-bucket',NULL,'test-videos/video3.mp4',NULL,'UPLOADED','NAME_FACING'),(NULL,NULL,NULL,'2026-02-05 12:40:47.701050',NULL,'2026-02-05 12:40:47.700050','2026-02-05 12:40:47.701050',_binary 'S=ItPO≤,\÷\÷D\ﬂ\‡',_binary '&;ÆG\‡\nE™k\’a\È?t',NULL,'test-bucket',NULL,'test-videos/video1.mp4',NULL,'UPLOADED','POSE_IMITATION'),(NULL,'2026-02-05 12:50:18.688742',NULL,'2026-02-05 12:41:46.413527',NULL,'2026-02-05 12:41:46.413527','2026-02-05 12:50:18.691386',_binary 'öññwñ.BèÉ\"{N\‡¨',_binary '3ó\·_ıOn†›≤ü¬ú',NULL,'test-bucket',NULL,'test-videos/video4.mp4','SUCCESS','UPLOADED','NAME_NON_FACING'),(NULL,'2026-02-05 12:50:07.383447',NULL,'2026-02-05 12:41:46.412524',NULL,'2026-02-05 12:41:46.412524','2026-02-05 12:50:07.385620',_binary 'öññwñ.BèÉ\"{N\‡¨',_binary 'R\¬]!( Jwè(Æ•ª~4\„',NULL,'test-bucket',NULL,'test-videos/video3.mp4','SUCCESS','UPLOADED','NAME_FACING'),(NULL,'2026-02-05 12:49:36.429002',NULL,'2026-02-05 12:41:46.412524',NULL,'2026-02-05 12:41:46.412015','2026-02-05 12:49:36.442683',_binary 'öññwñ.BèÉ\"{N\‡¨',_binary 'c\ÊQå6IIægOÛ\Œ\'d_',NULL,'test-bucket',NULL,'test-videos/video1.mp4','SUCCESS','UPLOADED','POSE_IMITATION'),(NULL,'2026-02-05 12:49:53.264255',NULL,'2026-02-05 12:41:46.412524',NULL,'2026-02-05 12:41:46.412524','2026-02-05 12:49:53.266251',_binary 'öññwñ.BèÉ\"{N\‡¨',_binary 'ìu\Àn\‘G®∫Ø\È#ã6\—',NULL,'test-bucket',NULL,'test-videos/video2.mp4','SUCCESS','UPLOADED','SPEECH_IMITATION'),(NULL,NULL,NULL,'2026-02-05 12:40:47.701050',NULL,'2026-02-05 12:40:47.701050','2026-02-05 12:40:47.701050',_binary 'S=ItPO≤,\÷\÷D\ﬂ\‡',_binary '\‰\¬˘ø8OC>ù1`ãÑ∏\ÕQ',NULL,'test-bucket',NULL,'test-videos/video4.mp4',NULL,'UPLOADED','NAME_NON_FACING');
/*!40000 ALTER TABLE `video` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-09 10:12:01
