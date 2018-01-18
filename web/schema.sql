drop table if exists user;
create table user (
	user_id integer primary key autoincrement,
	username text not null,
	email text not null,
	pw_hash text not null
);


drop table if exists shops;
create table shops (
	shop_id integer primary key autoincrement,
	north  float(7),
	east	float(7),
	shop_name  varchar(50),
	type	varchar(30),
	Review  integer
);

