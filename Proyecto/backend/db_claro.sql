-- Seleccionar la base de datos
USE db_claro;

-- Eliminar tablas existentes (en orden correcto por dependencias)
DROP TABLE IF EXISTS evidencias_servicio;
DROP TABLE IF EXISTS reagendamientos;
DROP TABLE IF EXISTS historial_visitas;
DROP TABLE IF EXISTS visitas;
DROP TABLE IF EXISTS tecnicos;
DROP TABLE IF EXISTS usuarios;

-- Crear base de datos
-- CREATE DATABASE IF NOT EXISTS db_claro;
-- USE db_claro;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre_usuario VARCHAR(100) NOT NULL,
    apellido_usuario VARCHAR(100) NOT NULL,
    rut_usuario VARCHAR(12) UNIQUE,
    email_usuario VARCHAR(100) UNIQUE NOT NULL,
    contraseña_hash VARCHAR(255) NOT NULL,
    rol ENUM('tecnico', 'auditor', 'admin') NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de técnicos
CREATE TABLE tecnicos (
    id_tecnico INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT UNIQUE NOT NULL,
    zona VARCHAR(50) NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- Tabla de visitas
CREATE TABLE visitas (
    id_visita INT PRIMARY KEY AUTO_INCREMENT,
    tecnico_id INT NOT NULL,
    cliente_nombre VARCHAR(100) NOT NULL,
    cliente_apellido VARCHAR(100) NOT NULL,
    cliente_direccion TEXT NOT NULL,
    cliente_comuna VARCHAR(50) NOT NULL,
    cliente_telefono VARCHAR(20) NOT NULL,
    fecha_programada DATE NOT NULL,
    hora_programada TIME NOT NULL,
    estado ENUM('programada', 'en_curso', 'completada', 'reagendada', 'cancelada') DEFAULT 'programada',
    tipo_servicio ENUM('instalacion', 'mantenimiento', 'reparacion', 'otro') NOT NULL,
    descripcion_servicio TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id_tecnico)
);

-- Tabla de reagendamientos
CREATE TABLE reagendamientos (
    id_reagendamiento INT PRIMARY KEY AUTO_INCREMENT,
    visita_id INT NOT NULL,
    fecha_anterior DATE NOT NULL,
    hora_anterior TIME NOT NULL,
    fecha_nueva DATE NOT NULL,
    hora_nueva TIME NOT NULL,
    motivo TEXT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (visita_id) REFERENCES visitas(id_visita) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario)
);

-- Tabla de historial_visitas
CREATE TABLE historial_visitas (
    id_historial INT PRIMARY KEY AUTO_INCREMENT,
    visita_id INT NOT NULL,
    accion ENUM('creada', 'reagendada', 'completada', 'nota_agregada', 'cancelada', 'estado_cambiado') NOT NULL,
    detalles TEXT,
    usuario_id INT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (visita_id) REFERENCES visitas(id_visita) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario)
);

-- Tabla de evidencias_servicio
CREATE TABLE evidencias_servicio (
    id_evidencia INT PRIMARY KEY AUTO_INCREMENT,
    visita_id INT NOT NULL,
    tipo_evidencia ENUM('foto', 'firma', 'comprobante', 'otro') NOT NULL DEFAULT 'foto',
    archivo_ruta VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT NOT NULL,
    FOREIGN KEY (visita_id) REFERENCES visitas(id_visita) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario)
);