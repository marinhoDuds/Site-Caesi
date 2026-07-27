CREATE TABLE `attachment_owner` (
    `id` BIGINT AUTO_INCREMENT,
    `owner_type` ENUM(
        'ticket', 'operation', 'information', 'post', 'administrator'
    ) NOT NULL,
    CONSTRAINT pk_attachment_owner PRIMARY KEY (id)
);

CREATE TABLE `ticket` (
    `id` BIGINT,
    `public_id` VARCHAR(16) COLLATE ascii_bin NOT NULL,
    `protocol` VARCHAR(20) NOT NULL,
    `semester` VARCHAR(10) NOT NULL,
    `content` VARCHAR(2200) NOT NULL,
    `ticket_type` ENUM(
        'classmates', 'infrastructure', 'professors', 'schedules', 'student_groups', 'subjects', 'other'
    ) NOT NULL,
    `author` VARCHAR(120),
    `email` VARCHAR(255),
    `status` VARCHAR(50) DEFAULT 'Aberto',
    `password` VARCHAR(32) DEFAULT NULL,
    `admin_notes` VARCHAR(2200),
    `updated_at` DATE,
    CONSTRAINT pk_ticket PRIMARY KEY (id),
    CONSTRAINT fk_ticket_attachment_owner_id FOREIGN KEY (id) REFERENCES attachment_owner(id),
    CONSTRAINT unique_ticket_public_id UNIQUE (public_id),
    CONSTRAINT unique_ticket_protocol UNIQUE (protocol)
);

CREATE TABLE `operation` (
    `id` BIGINT,
    `created_at` DATE NOT NULL,
    `value` FLOAT NOT NULL,
    `description` VARCHAR(2200) NOT NULL,
    `operation_type` ENUM(
        'aid', 'events', 'incomes', 'infrastructure', 'procurement', 'reimbursement', 'other'
    ) NOT NULL,
    `previous` BIGINT,
    CONSTRAINT pk_operation PRIMARY KEY (id),
    CONSTRAINT fk_operation_attachment_owner_id FOREIGN KEY (id) REFERENCES attachment_owner(id),
    CONSTRAINT fk_operation_operation_id FOREIGN KEY (previous) REFERENCES operation(id)
);

CREATE TABLE `information` (
    `id` BIGINT,
    `content` MEDIUMTEXT NOT NULL,
    `information_type` VARCHAR(100) NOT NULL,
    CONSTRAINT pk_information PRIMARY KEY (id),
    CONSTRAINT fk_information_attachment_owner_id FOREIGN KEY (id) REFERENCES attachment_owner(id)
);

CREATE TABLE `post` (
    `id` BIGINT,
    `title` VARCHAR(255) NOT NULL,
    `post_type` VARCHAR(100) NOT NULL,
    `created_at` DATE NOT NULL,
    `updated_at` DATE,
    `caption` VARCHAR(2200),
    CONSTRAINT pk_post PRIMARY KEY (id),
    CONSTRAINT fk_post_attachment_owner_id FOREIGN KEY (id) REFERENCES attachment_owner(id)
);

-- TODO: talvez adicionar public_id nanoID
CREATE TABLE `administrator` (
    `id` BIGINT,
    `name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `semester` VARCHAR(4),
    `bio` VARCHAR(200),
    `linkedin` VARCHAR(2083),
    `github` VARCHAR(2083),
    `lattes` VARCHAR(2083),
    CONSTRAINT pk_administrator PRIMARY KEY (id),
    CONSTRAINT fk_administrator_attachment_owner_id FOREIGN KEY (id) REFERENCES attachment_owner(id)
);

-- TODO: ver sobre hash da url gerada pelo S3, pra poder fazer UNIQUE KEY com owner_id
CREATE TABLE `attachment` (
    `id` BIGINT AUTO_INCREMENT,
    `owner_id` BIGINT NOT NULL,
    `object_key` VARCHAR(1024) NOT NULL,
    `filename` VARCHAR(255) NOT NULL,
    `content_type` VARCHAR(255) NOT NULL,
    CONSTRAINT pk_attachment PRIMARY KEY (id),
    CONSTRAINT fk_attachment_attachment_owner_id FOREIGN KEY (owner_id) REFERENCES attachment_owner(id)
);

CREATE TABLE `event` (
    `id` BIGINT AUTO_INCREMENT,
    `title` VARCHAR(255) NOT NULL,
    `scheduled_to` DATE NOT NULL,
    `start_time` VARCHAR(10) DEFAULT NULL,
    `end_time` VARCHAR(10) DEFAULT NULL,
    `location` VARCHAR(255) DEFAULT NULL,
    `category` VARCHAR(50) DEFAULT 'CAESI',
    `description` VARCHAR(200),
    `formulario_id` BIGINT DEFAULT NULL,
    CONSTRAINT pk_event PRIMARY KEY (id)
);
