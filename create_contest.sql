DROP DATABASE IF EXISTS DATABASE_NAME;
CREATE DATABASE DATABASE_NAME;
use DATABASE_NAME;

CREATE TABLE `contest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `carID` int(11) NOT NULL,
  `teamName` varchar(45) NOT NULL,
  `startTimeStamp` datetime(6) DEFAULT NULL,
  `firstLapTimeStamp` datetime(6) DEFAULT NULL,
  `secondLapTimeStamp` datetime(6) DEFAULT NULL,
  `thirdLapTimeStamp` datetime(6) DEFAULT NULL,
  `penalty` int(11) DEFAULT '0',
  `disqualified` tinyint(4) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;
