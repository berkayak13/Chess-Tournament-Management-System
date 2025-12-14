INSERT INTO users (username, password, role) VALUES
  -- managers
  ('kevin',      'K3v!n#2024',    'manager'),
  ('bob',        'Bob@Secure88',   'manager'),
  ('admin1',     '326593',         'manager'),
  ('jessica',    'secretpw.33#',   'manager'),
  ('admin2',     'admin2pw',       'manager'),
  ('fatima',     'F4tima!DBmngr',  'manager'),
  ('yusuf',      'Yu$ufSecure1',   'manager'),
  ('maria',      'M@r1a321',       'manager'),

  -- players
  ('alice',      'Pass@123',       'player'),
  ('bob1',       'Bob@2023',       'player'),
  ('clara',      'Clara#21',       'player'),
  ('david',      'D@vid2024',      'player'),
  ('emma',       'Emm@9win',       'player'),
  ('felix',      'F3lix$88',       'player'),
  ('grace',      'Gr@ce2025',      'player'),
  ('henry',      'Hen!ry777',      'player'),
  ('isabel',     'Isa#Blue',       'player'),
  ('jack',       'Jack@321',       'player'),
  ('kara',       'Kara$99',        'player'),
  ('liam',       'Li@mChess',      'player'),
  ('mia',        'M!a2020',        'player'),
  ('noah',       'Noah#44',        'player'),
  ('olivia',     'Oliv@99',        'player'),
  ('peter',      'P3ter!1',        'player'),
  ('quinn',      'Quinn%x',        'player'),
  ('rachel',     'Rach3l@',        'player'),
  ('sam',        'S@mWise',        'player'),
  ('tina',       'T!naChess',      'player'),
  ('umar',       'Umar$22',        'player'),
  ('vera',       'V3ra#21',        'player'),
  ('will',       'Will@321',       'player'),
  ('xena',       'Xena$!',         'player'),
  ('yusuff',     'Yusuf88@',       'player'),
  ('zoe',        'Zo3!pass',       'player'),
  ('hakan',      'H@kan44',        'player'),
  ('julia',      'J!ulia77',       'player'),
  ('mehmet',     'Mehmet#1',       'player'),
  ('elena',      'El3na@pw',       'player'),
  ('nina',       'Nina@2024',      'player'),
  ('louis',      'Louis#88',       'player'),
  ('sofia',      'Sofia$22',       'player'),
  ('ryan',       'Ryan@77',        'player'),
  ('claire',     'Claire#01',      'player'),
  ('jacob',      'Jacob!pass',     'player'),
  ('ava',        'Ava@Chess',      'player'),
  ('ethan',      'Ethan$win',      'player'),
  ('isabella',   'Isabella#77',    'player'),
  ('logan',      'Logan@55',       'player'),
  ('sophia',     'Sophia$12',      'player'),
  ('lucas',      'Lucas!88',       'player'),
  ('harper',     'Harper@pw',      'player'),
  ('jamess',     'James!44',       'player'),
  ('amelia',     'Amelia#99',      'player'),
  ('benjamin',   'Ben@2023',       'player'),
  ('ella',       'Ella@pw',        'player'),
  ('alex',       'Alex$88',        'player'),
  ('lily',       'Lily@sun',       'player'),

  -- coaches
  ('carol',      'coachpw',        'coach'),
  ('david_b',    'dPass!99',       'coach'),
  ('emma_green', 'E@mma77',        'coach'),
  ('fatih',      'FatihC21',       'coach'),
  ('hana',       'Hana$45',        'coach'),
  ('lucaas',     'Lucas#1',        'coach'),
  ('mia_rose',   'Mia!888',        'coach'),
  ('onur',       'onUr@32',        'coach'),
  ('sofia_lop',  'S0fia#',         'coach'),
  ('arslan_yusuf','Yusuf199',      'coach'),

  -- arbiters
  ('erin',       'arbpw',          'arbiter'),
  ('mark',       'refpass',        'arbiter'),
  ('lucy',       'arb123',         'arbiter'),
  ('ahmet',      'pass2024',       'arbiter'),
  ('ana',        'secretpw',       'arbiter'),
  ('james',      'secure1',        'arbiter'),
  ('sara',       'sara!2024',      'arbiter'),
  ('mohamed',    'mpass',          'arbiter');


 
INSERT INTO managers (username, password) VALUES
  ('kevin',    'K3v!n#2024'),
  ('bob',      'Bob@Secure88'),
  ('admin1',   '326593'),
  ('jessica',  'secretpw.33#'),
  ('admin2',   'admin2pw'),
  ('fatima',   'F4tima!DBmngr'),
  ('yusuf',    'Yu$ufSecure1'),
  ('maria',    'M@r1a321');
 
  INSERT INTO title (title_ID, title_name) VALUES
  (1, 'Grandmaster'),
  (2, 'International Master'),
  (3, 'FIDE Master'),
  (4, 'Candidate Master'),
  (5, 'National Master');

INSERT INTO sponsors (sponsor_ID, sponsor_name) VALUES  (100, 'ChessVision'),  (101, 'Grandmaster Corp'),  (102, 'Queen''s Gambit Ltd.'),  (103, 'MateMate Inc.'),  (104, 'RookTech'),  (105, 'PawnPower Solutions'),  (106, 'CheckSecure AG'),  (107, 'Endgame Enterprises'),  (108, 'King''s Arena Foundation');

INSERT INTO teams (team_ID, team_name, sponsor_ID) VALUES  (1,  'Knights',       100),  (2,  'Rooks',         101),  (3,  'Bishops',       102),  (4,  'Pawns',         100),  (5,  'Queens',        103),  (6,  'Kings',         104),  (7,  'Castles',       101),  (8,  'Checkmates',    105),  (9,  'En Passants',   106),  (10, 'Blitz Masters', 107);

INSERT INTO coaches (
  username,
  password,
  name,
  surname,
  nationality,
  team_id,
  contract_start,
  contract_finish
) VALUES
  ('carol',        'coachpw',  'Carol', 'White',  'Canada',  1, '2023-01-01', '2026-01-01'),
  ('david_b',      'dPass!99', 'David', 'Brown',  'USA',     2, '2024-02-15', '2026-02-15'),
  ('emma_green',   'E@mma77',  'Emma',  'Green',  'UK',      3, '2022-03-01', '2025-03-01'),
  ('fatih',        'FatihC21', 'Fatih', 'Ceylan', 'Turkey',  4, '2024-05-10', '2026-05-10'),
  ('hana',         'Hana$45',  'Hana',  'Yamada', 'Japan',   5, '2023-04-01', '2024-10-01'),
  ('lucaas',       'Lucas#1',  'Lucas', 'Müller', 'Germany', 6, '2024-01-01', '2025-01-01'),
  ('mia_rose',     'Mia!888',  'Mia',   'Rossi',  'Italy',   7, '2024-06-01', '2025-06-01'),
  ('onur',         'onUr@32',  'Onur',  'Kaya',   'Turkey',  8, '2023-03-15', '2025-09-15'),
  ('sofia_lop',    'S0fia#',   'Sofia', 'López',  'Spain',   9, '2024-05-01', '2025-11-01'),
  ('arslan_yusuf', 'Yusuf199', 'Yusuf', 'Arslan', 'Turkey', 10, '2024-02-01', '2026-08-01');

 
 
INSERT INTO coach_certifications (coach_username, certification) VALUES  ('carol',        'FIDE Certified'),  ('carol',        'National Level'),  ('david_b',      'National Level'),  ('emma_green',   'FIDE Certified'),  ('fatih',        'National Level'),  ('hana',         'Regional Certified'),  ('lucaas',       'Club Level'),  ('lucaas',       'Regional Certified'),  ('mia_rose',     'FIDE Certified'),  ('onur',         'National Level'),  ('sofia_lop',    'Regional Certified'),  ('arslan_yusuf', 'Club Level'),  ('arslan_yusuf', 'National Level');

INSERT INTO arbiters (
  username,
  password,
  name,
  surname,
  nationality,
  experience_level
) VALUES
  ('erin',    'arbpw',    'Erin',    'Gray',   'Germany',    'advanced'),
  ('mark',    'refpass',  'Mark',    'Blake',  'USA',        'intermediate'),
  ('lucy',    'arb123',   'Lucy',    'Wang',   'China',      'expert'),
  ('ahmet',   'pass2024', 'Ahmet',   'Yılmaz', 'Turkey',     'beginner'),
  ('ana',     'secretpw', 'Ana',     'Costa',  'Brazil',     'advanced'),
  ('james',   'secure1',  'James',   'Taylor', 'UK',         'intermediate'),
  ('sara',    'sara!2024','Sara',    'Kim',    'South Korea','expert'),
  ('mohamed', 'mpass',    'Mohamed', 'Farouk', 'Egypt',      'advanced');


INSERT INTO arbiter_certifications (username, certification) VALUES  ('erin',    'FIDE Certified'),  ('mark',    'National Arbiter'),  ('lucy',    'International Arbiter'),  ('ahmet',   'Local Certification'),  ('ana',     'FIDE Certified'),  ('james',   'Regional Certification'),  ('sara',    'International Arbiter'),  ('mohamed', 'National Arbiter');

INSERT INTO halls (hall_ID, hall_name, hall_country, hall_capacity) VALUES  (1,  'Grandmaster Arena',   'USA',    10),  (2,  'Royal Chess Hall',    'UK',      8),  (3,  'FIDE Dome',           'Germany',12),  (4,  'Masters Pavilion',    'Turkey',  6),  (5,  'Checkmate Center',    'France',  9),  (6,  'ELO Stadium',         'Spain',  10),  (7,  'Tactical Grounds',    'Italy',   7),  (8,  'Endgame Hall',        'India',   8),  (9,  'Strategic Square',    'Canada',  6),  (10, 'Opening Hall',        'Japan',   5);

INSERT INTO match_tables (table_id, hall_id) VALUES  (1,  1),  (2,  1),  (3,  1),  (4,  2),  (5,  2),  (6,  3),  (7,  3),  (8,  3),  (9,  4),  (10, 5),  (11, 6),  (12, 6),  (13, 7),  (14, 8),  (15, 9),  (16,10);

INSERT INTO matches (  match_id,  date,  time_slot,  hall_id,  table_id,  team1_id,  team2_id,  arbiter_username,  ratings) VALUES  (1,  '2025-02-01', '01:00:00',  1,  1,  1,  2, 'erin',   8.2),  (2,  '2025-02-01', '03:00:00',  1,  2,  3,  4, 'lucy',   7.9),  (3,  '2025-02-02', '01:00:00',  1,  3,  5,  6, 'mark',   NULL),  (4,  '2025-02-02', '03:00:00',  2,  4,  7,  8, 'erin',   8.5),  (5,  '2025-02-03', '01:00:00',  2,  5,  9, 10, 'lucy',   NULL),  (6,  '2025-02-03', '03:00:00',  3,  6,  1,  3, 'mohamed',NULL),  (7,  '2025-02-04', '01:00:00',  3,  7,  2,  5, 'erin',   4.5),  (8,  '2025-02-04', '03:00:00',  3,  8,  6,  7, 'sara',   3.1),  (9,  '2025-02-05', '01:00:00',  4,  9,  8,  9, 'ana',    7.7),  (10, '2025-02-05', '03:00:00',  5, 10, 10,  1, 'mark',   6.4),  (11, '2025-02-06', '01:00:00',  6, 11,  3,  5, 'james',  5.1),  (12, '2025-02-06', '03:00:00',  6, 12,  4,  6, 'lucy',   NULL),  (13, '2025-02-07', '01:00:00',  7, 13,  7,  9, 'sara',   NULL),  (14, '2025-02-07', '03:00:00',  8, 14,  8, 10, 'mohamed',2.6),  (15, '2025-02-08', '01:00:00',  9, 15,  1,  4, 'erin',   7.1),  (16, '2025-02-08', '03:00:00', 10, 16,  2,  5, 'ana',    6.3),  (17, '2025-02-09', '01:00:00', 10, 16,  3,  6, 'james',  NULL),  (18, '2025-02-09', '03:00:00',  8, 14,  7, 10, 'mark',   4.9),  (19, '2025-02-10', '01:00:00',  7, 13,  5,  8, 'lucy',   9.7),  (20, '2025-02-10', '03:00:00',  3,  8,  6,  9, 'ahmet',  7.4);

INSERT INTO players (
  username,
  password,
  name,
  surname,
  nationality,
  dateofbirth,
  elorating,
  fideid,
  titleid,
  team_list
) VALUES
  ('alice',    'Pass@123',    'Alice',    'Smith',     'USA',        '2000-05-10', 2200, 'FIDE001', 1, ''),
  ('bob1',     'Bob@2023',    'Bob',      'Jones',     'UK',         '1998-07-21', 2100, 'FIDE002', 5, ''),
  ('clara',    'Clara#21',    'Clara',    'Kim',       'KOR',        '2001-03-15', 2300, 'FIDE003', 2, ''),
  ('david',    'D@vid2024',   'David',    'Chen',      'CAN',        '1997-12-02', 2050, 'FIDE004', 3, ''),
  ('emma',     'Emm@9win',    'Emma',     'Rossi',     'ITA',        '1999-06-19', 2250, 'FIDE005', 2, ''),
  ('felix',    'F3lix$88',    'Felix',    'Novak',     'GER',        '2002-09-04', 2180, 'FIDE006', 4, ''),
  ('grace',    'Gr@ce2025',   'Grace',    'Ali',       'TUR',        '2000-08-12', 2320, 'FIDE007', 1, ''),
  ('henry',    'Hen!ry777',   'Henry',    'Patel',     'IND',        '1998-04-25', 2150, 'FIDE008', 3, ''),
  ('isabel',   'Isa#Blue',    'Isabel',   'Lopez',     'MEX',        '2001-02-17', 2240, 'FIDE009', 3, ''),
  ('jack',     'Jack@321',    'Jack',     'Brown',     'USA',        '1997-11-30', 2000, 'FIDE010', 4, ''),
  ('kara',     'Kara$99',     'Kara',     'Singh',     'IND',        '2003-01-07', 2350, 'FIDE011', 5, ''),
  ('liam',     'Li@mChess',   'Liam',     'Müller',    'GER',        '1999-05-23', 2200, 'FIDE012', 2, ''),
  ('mia',      'M!a2020',     'Mia',      'Wang',      'CHN',        '2002-12-14', 2125, 'FIDE013', 4, ''),
  ('noah',     'Noah#44',     'Noah',     'Evans',     'CAN',        '1996-08-08', 2400, 'FIDE014', 1, ''),
  ('olivia',   'Oliv@99',     'Olivia',   'Taylor',    'UK',         '2001-06-03', 2280, 'FIDE015', 2, ''),
  ('peter',    'P3ter!1',     'Peter',    'Dubois',    'FRA',        '2000-10-11', 2140, 'FIDE016', 3, ''),
  ('quinn',    'Quinn%x',     'Quinn',    'Ma',        'CHN',        '1998-09-16', 2210, 'FIDE017', 4, ''),
  ('rachel',   'Rach3l@',     'Rachel',   'Silva',     'BRA',        '1999-07-06', 2290, 'FIDE018', 2, ''),
  ('sam',      'S@mWise',     'Sam',      'O''Neill',  'IRE',        '2002-01-29', 2100, 'FIDE019', 3, ''),
  ('tina',     'T!naChess',   'Tina',     'Zhou',      'KOR',        '2003-03-13', 2230, 'FIDE020', 3, ''),
  ('umar',     'Umar$22',     'Umar',     'Haddad',    'UAE',        '1997-11-01', 2165, 'FIDE021', 4, ''),
  ('vera',     'V3ra#21',     'Vera',     'Nowak',     'POL',        '2001-04-22', 2260, 'FIDE022', 2, ''),
  ('will',     'Will@321',    'Will',     'Johnson',   'AUS',        '2000-06-18', 2195, 'FIDE023', 3, ''),
  ('xena',     'Xena$!',      'Xena',     'Popov',     'RUS',        '1998-02-09', 2330, 'FIDE024', 1, ''),
  ('yusuff',   'Yusuf88@',    'Yusuf',    'Demir',     'TUR',        '1999-12-26', 2170, 'FIDE025', 4, ''),
  ('zoe',      'Zo3!pass',    'Zoe',      'Tanaka',    'JPN',        '2001-05-05', 2220, 'FIDE026', 2, ''),
  ('hakan',    'H@kan44',     'Hakan',    'Şimşek',    'TUR',        '1997-10-14', 2110, 'FIDE027', 4, ''),
  ('julia',    'J!ulia77',    'Julia',    'Nilsen',    'SWE',        '2002-03-02', 2300, 'FIDE028', 1, ''),
  ('mehmet',   'Mehmet#1',    'Mehmet',   'Yıldız',    'TUR',        '1998-07-31', 2080, 'FIDE029', 3, ''),
  ('elena',    'El3na@pw',    'Elena',    'Kuznetsova','RUS',        '2000-09-24', 2345, 'FIDE030', 1, ''),
  ('nina',     'Nina@2024',   'Nina',     'Martinez',  'ESP',        '2001-07-12', 2150, 'FIDE031', 3, ''),
  ('louis',    'Louis#88',    'Louis',    'Schneider', 'GER',        '1998-11-08', 2100, 'FIDE032', 4, ''),
  ('sofia',    'Sofia$22',    'Sofia',    'Russo',     'ITA',        '2000-02-17', 2250, 'FIDE033', 2, ''),
  ('ryan',     'Ryan@77',     'Ryan',     'Edwards',   'USA',        '1997-09-02', 2170, 'FIDE034', 3, ''),
  ('claire',   'Claire#01',   'Claire',   'Dupont',    'FRA',        '2002-01-11', 2225, 'FIDE035', 2, ''),
  ('jacob',    'Jacob!pass',  'Jacob',    'Green',     'AUS',        '1999-10-20', 2120, 'FIDE036', 4, ''),
  ('ava',      'Ava@Chess',   'Ava',      'Kowalski',  'POL',        '2003-05-04', 2300, 'FIDE037', 2, ''),
  ('ethan',    'Ethan$win',   'Ethan',    'Yamamoto',  'JPN',        '1998-03-25', 2190, 'FIDE038', 3, ''),
  ('isabella', 'Isabella#77', 'Isabella', 'Moretti',   'ITA',        '2001-08-19', 2240, 'FIDE039', 2, ''),
  ('logan',    'Logan@55',    'Logan',    'O''Connor', 'IRL',        '1997-04-14', 2115, 'FIDE040', 4, ''),
  ('sophia',   'Sophia$12',   'Sophia',   'Weber',     'GER',        '2000-06-01', 2280, 'FIDE041', 2, ''),
  ('lucas',    'Lucas!88',    'Lucas',    'Novak',     'CZE',        '1999-12-30', 2145, 'FIDE042', 4, ''),
  ('harper',   'Harper@pw',   'Harper',   'Clarke',    'UK',         '2002-07-06', 2200, 'FIDE043', 2, ''),
  ('jamess',   'James!44',    'James',    'Silva',     'BRA',        '1998-03-21', 2155, 'FIDE044', 3, ''),
  ('amelia',   'Amelia#99',   'Amelia',   'Zhang',     'CHN',        '2001-09-09', 2275, 'FIDE045', 2, ''),
  ('benjamin', 'Ben@2023',    'Benjamin', 'Fischer',   'GER',        '1997-01-27', 2095, 'FIDE046', 4, ''),
  ('ella',     'Ella@pw',     'Ella',     'Svensson',  'SWE',        '2000-11-03', 2235, 'FIDE047', 2, ''),
  ('alex',     'Alex$88',     'Alex',     'Dimitrov',  'BUL',        '1999-05-22', 2180, 'FIDE048', 3, ''),
  ('lily',     'Lily@sun',    'Lily',     'Nakamura',  'USA',        '2003-02-12', 2310, 'FIDE049', 2, '');


INSERT INTO player_teams (username, team_id) VALUES
  ('alice',    1),
  ('bob1',     2),
  ('clara',    3),
  ('david',    4),
  ('emma',     5),
  ('felix',    6),
  ('grace',    7),
  ('henry',    8),
  ('isabel',   9),
  ('jack',    10),
  ('kara',     1),
  ('liam',     2),
  ('mia',      3),
  ('noah',     4),
  ('olivia',   5),
  ('peter',    6),
  ('quinn',    7),
  ('rachel',   8),
  ('sam',      9),
  ('tina',    10),
  ('umar',     1),
  ('vera',     2),
  ('will',     3),
  ('xena',     4),
  ('yusuff',   5),
  ('zoe',      6),
  ('hakan',    7),
  ('julia',    8),
  ('mehmet',   9),
  ('elena',   10),
  ('nina',     1),
  ('louis',    2),
  ('sofia',    3),
  ('ryan',     4),
  ('claire',   5),
  ('jacob',    6),
  ('ava',      7),
  ('ethan',    8),
  ('isabella', 9),
  ('logan',   10),
  ('sophia',   1),
  ('lucas',    2),
  ('harper',   3),
  ('amelia',   5),
  ('benjamin', 6),
  ('ella',     7),
  ('alex',     8),
  ('lily',     9);

-- Match assignments aligned with teams:
-- match_id -> (team1, team2): white must be in team1, black must be in team2
INSERT INTO match_assignments (match_id, white_player, black_player, result) VALUES
  (1,  'alice',    'bob1',     'draw'),        -- team1=1, team2=2
  (2,  'clara',    'david',    'black wins'),  -- team1=3, team2=4
  (3,  'emma',     'felix',    'black wins'),  -- team1=5, team2=6
  (4,  'grace',    'henry',    'draw'),        -- team1=7, team2=8
  (5,  'isabel',   'jack',     'black wins'),  -- team1=9, team2=10
  (6,  'kara',     'mia',      'white wins'),  -- team1=1, team2=3
  (7,  'liam',     'olivia',   'black wins'),  -- team1=2, team2=5
  (8,  'peter',    'quinn',    'white wins'),  -- team1=6, team2=7
  (9,  'rachel',   'sam',      'black wins'),  -- team1=8, team2=9
  (10, 'tina',     'umar',     'black wins'),  -- team1=10, team2=1
  (11, 'will',     'yusuff',   'white wins'),  -- team1=3, team2=5
  (12, 'noah',     'zoe',      'white wins'),  -- team1=4, team2=6
  (13, 'hakan',    'mehmet',   'black wins'),  -- team1=7, team2=9
  (14, 'julia',    'elena',    'draw'),        -- team1=8, team2=10
  (15, 'nina',     'xena',     'draw'),        -- team1=1, team2=4
  (16, 'vera',     'claire',   'white wins'),  -- team1=2, team2=5
  (17, 'sofia',    'jacob',    'black wins'),  -- team1=3, team2=6
  (18, 'ava',      'logan',    'black wins'),  -- team1=7, team2=10
  (19, 'amelia',   'alex',     'black wins'),  -- team1=5, team2=8
  (20, 'benjamin', 'isabella', 'white wins');  -- team1=6, team2=9

