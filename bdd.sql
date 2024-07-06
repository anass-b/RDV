create database if not exists doctor_appointments;
use doctor_appointments;
create table admins (
    id int primary key auto_increment,
    nom varchar(255),
    prenom varchar(255),
    email varchar(255),
    mdp varchar(255)
);
create table patients (
    id int primary key auto_increment,
    nom varchar(255),
    prenom varchar(255),
    email varchar(255),
    mdp varchar(255),
    date_naissance date, 
    CNIE varchar(50),
    num_tel int 
);
create table appointments (
    id int primary key auto_increment,
    date_appointment date ,
    heure_appointment time ,
    durée int , 
    patient_id int , 
    status enum('pending','accepted','refused') default 'pending',
    foreign key (patient_id) references patients(id)
);
