drop table if exists config;
drop table if exists users;

create table config (
	user_id integer primary key,
	zipcode integer not null,
	celsius boolean not null default 1,
	user_location_name text not null,
	auto_location_name text not null,
	mode integer not null,
	set_temp integer not null,
	status boolean not null default 0
);

create table users (
	user_id integer primary key autoincrement,
	name text not null,
	email text not null
);
