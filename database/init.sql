CREATE DATABASE IF NOT EXISTS library_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE library_system;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('user','admin') NOT NULL DEFAULT 'user' COMMENT 'admin=管理员',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS books (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  author VARCHAR(100) DEFAULT '',
  isbn VARCHAR(20) DEFAULT '',
  category VARCHAR(50) DEFAULT '',
  cover_url VARCHAR(500) DEFAULT '',
  description TEXT,
  is_online TINYINT(1) DEFAULT 0 COMMENT '1=在线图书 0=实体图书',
  online_url VARCHAR(500) DEFAULT '' COMMENT '在线阅读地址',
  total_copies INT DEFAULT 0 COMMENT '实体馆藏总数',
  available_copies INT DEFAULT 0 COMMENT '当前可预约数量',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservations (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  book_id BIGINT NOT NULL,
  status ENUM('pending','borrowed','returned','cancelled') DEFAULT 'pending' COMMENT 'pending=待审核 borrowed=借阅中 returned=已归还 cancelled=已取消',
  reserved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  borrowed_at DATETIME NULL COMMENT '出借时间',
  due_date DATETIME NULL COMMENT '应还时间 = 出借时间 + 7天',
  reminded TINYINT(1) DEFAULT 0 COMMENT '到期前1天是否已发提醒邮件',
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (book_id) REFERENCES books(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS email_codes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(100) NOT NULL,
  code VARCHAR(6) NOT NULL,
  purpose ENUM('register','reset') DEFAULT 'register',
  used TINYINT(1) DEFAULT 0,
  expires_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 在线图书（公版书全文由 scripts/download_books.py 下载到 backend/static/books/）
INSERT INTO books (title, author, category, cover_url, description, is_online, online_url) VALUES
('红楼梦', '曹雪芹', '古典文学', '/static/covers/hongloumeng.svg', '中国古典四大名著之首，章回体长篇小说', 1, '/static/books/hongloumeng.txt'),
('西游记', '吴承恩', '古典文学', '/static/covers/xiyouji.svg', '神魔章回体长篇小说', 1, '/static/books/xiyouji.txt'),
('三国演义', '罗贯中', '古典文学', '/static/covers/sanguoyanyi.svg', '历史演义小说经典', 1, '/static/books/sanguoyanyi.txt'),
('水浒传', '施耐庵', '古典文学', '/static/covers/shuihuzhuan.svg', '英雄传奇章回体长篇小说', 1, '/static/books/shuihuzhuan.txt'),
('Pride and Prejudice', 'Jane Austen', '英文经典', '/static/covers/pride-and-prejudice.jpg', 'Classic romance novel', 1, '/static/books/pride-and-prejudice.txt'),
('Alice''s Adventures in Wonderland', 'Lewis Carroll', '英文经典', '/static/covers/alice-in-wonderland.jpg', 'Children''s fantasy novel', 1, '/static/books/alice-in-wonderland.txt'),
('Frankenstein', 'Mary Shelley', '英文经典', '/static/covers/frankenstein.jpg', 'Gothic science fiction', 1, '/static/books/frankenstein.txt'),
('The Adventures of Sherlock Holmes', 'Arthur Conan Doyle', '英文经典', '/static/covers/sherlock-holmes.jpg', 'Detective short stories', 1, '/static/books/sherlock-holmes.txt'),
('Moby Dick', 'Herman Melville', '英文经典', '/static/covers/moby-dick.jpg', 'Adventure of the whaling ship Pequod', 1, '/static/books/moby-dick.txt'),
('A Tale of Two Cities', 'Charles Dickens', '英文经典', '/static/covers/a-tale-of-two-cities.jpg', 'Historical novel of the French Revolution', 1, '/static/books/a-tale-of-two-cities.txt');

-- 实体图书（供预约借阅）
INSERT INTO books (title, author, category, cover_url, description, is_online, total_copies, available_copies) VALUES
('数据库系统概论', '王珊', '教材', '/static/covers/db-system.svg', '数据库经典教材', 0, 5, 5),
('算法导论', 'Thomas H. Cormen', '计算机科学', '/static/covers/introduction-to-algorithms.svg', '算法领域权威著作', 0, 3, 3),
('深入理解计算机系统', 'Randal E. Bryant', '计算机科学', '/static/covers/csapp.svg', 'CSAPP，程序员必修', 0, 4, 4),
('计算机网络：自顶向下方法', 'James F. Kurose', '计算机科学', '/static/covers/computer-networking.svg', '计算机网络经典教材', 0, 3, 3),
('现代操作系统', 'Andrew S. Tanenbaum', '计算机科学', '/static/covers/modern-operating-systems.svg', '操作系统权威教材', 0, 2, 2);
