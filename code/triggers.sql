-- ============================================================================
-- System Stats Table (for VM Worker aggregations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_stats (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    stat_name VARCHAR(100) NOT NULL,
    stat_value TEXT NOT NULL,
    stat_category VARCHAR(50) DEFAULT 'general',
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stat_name (stat_name),
    INDEX idx_category (stat_category),
    INDEX idx_computed_at (computed_at)
) ENGINE=InnoDB;

-- ============================================================================

DELIMITER $$

-- Trigger: Prevent overlapping coach contracts (no coach on multiple teams during overlapping dates)
CREATE TRIGGER trg_coach_no_overlap
BEFORE INSERT ON coaches
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT DEFAULT 0;
    -- Count any existing contract for this coach that overlaps the new contract period
    SELECT COUNT(*)
      INTO conflict_count
      FROM coaches
     WHERE username = NEW.username
       AND (
            NEW.contract_start <= contract_finish
            AND NEW.contract_finish >= contract_start
           );
    IF conflict_count > 0 THEN
       SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Violation: Coach cannot manage multiple teams with overlapping contracts';
    END IF;
END$$

-- Trigger: Also enforce no overlapping coach contracts on updates (if contract dates or team are modified)
CREATE TRIGGER trg_coach_no_overlap_upd
BEFORE UPDATE ON coaches
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT DEFAULT 0;
    -- Count overlapping contracts for this coach, excluding this current record
    SELECT COUNT(*)
      INTO conflict_count
      FROM coaches
     WHERE username = NEW.username
       AND NOT (username = OLD.username
                AND team_id = OLD.team_id
                AND contract_start = OLD.contract_start
                AND contract_finish = OLD.contract_finish)
       AND (
            NEW.contract_start <= contract_finish
            AND NEW.contract_finish >= contract_start
           );
    IF conflict_count > 0 THEN
       SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Violation: Coach cannot manage multiple teams with overlapping contracts';
    END IF;
END$$

-- Trigger: Prevent arbiter assignment conflicts and premature ratings on match insertion
CREATE TRIGGER trg_match_check_insert
BEFORE INSERT ON matches
FOR EACH ROW
BEGIN
    -- Arbiter conflict: ensure arbiter has no match overlapping this date/time
    IF EXISTS (
         SELECT 1 FROM matches m
          WHERE m.arbiter_username = NEW.arbiter_username
            AND m.date = NEW.date
            AND ( NEW.time_slot < ADDTIME(m.time_slot, '02:00:00')
                  AND m.time_slot < ADDTIME(NEW.time_slot, '02:00:00') )
       )
    THEN
       SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Violation: Arbiter is already assigned to a match at overlapping time slot';
    END IF;
    -- Ratings rule: ensure no rating is given at match creation unless match date has passed
    IF NEW.ratings IS NOT NULL THEN
       IF NEW.date >= CURDATE() THEN
          SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Violation: Cannot set match rating before the match date has passed';
       END IF;
       -- (If NEW.date is past, we allow insertion with a rating, assuming it's a completed match record)
    END IF;
END$$

-- Trigger: Prevent arbiter conflicts and improper rating changes on match updates
CREATE TRIGGER trg_match_check_update
BEFORE UPDATE ON matches
FOR EACH ROW
BEGIN
    -- Arbiter conflict: if arbiter or time/date is changed, check no overlap with another match
    IF (NEW.arbiter_username <> OLD.arbiter_username)
        OR (NEW.date <> OLD.date) OR (NEW.time_slot <> OLD.time_slot) THEN
        IF EXISTS (
             SELECT 1 FROM matches m
              WHERE m.arbiter_username = NEW.arbiter_username
                AND m.date = NEW.date
                AND m.match_id <> OLD.match_id  -- exclude current match
                AND ( NEW.time_slot < ADDTIME(m.time_slot, '02:00:00')
                      AND m.time_slot < ADDTIME(NEW.time_slot, '02:00:00') )
           )
        THEN
           SIGNAL SQLSTATE '45000'
             SET MESSAGE_TEXT = 'Violation: Arbiter is already assigned to a match at overlapping time slot';
        END IF;
    END IF;
    -- Ratings rule: prevent changing an already-submitted rating
    IF OLD.ratings IS NOT NULL THEN
       IF NEW.ratings <> OLD.ratings THEN
          SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Violation: Match rating has already been submitted and cannot be changed';
       END IF;
    ELSE
       -- If no rating yet, allow setting one only after match date and only once
       IF NEW.ratings IS NOT NULL THEN
          IF NEW.date >= CURDATE() THEN
             SIGNAL SQLSTATE '45000'
               SET MESSAGE_TEXT = 'Violation: Cannot submit rating before the match date has passed';
          END IF;
          -- (Note: The check that the correct arbiter submits the rating is handled in the procedure)
       END IF;
    END IF;
END$$

-- Trigger: Prevent players from being in overlapping matches; ensure players belong to correct teams
CREATE TRIGGER trg_player_assignment_check
BEFORE INSERT ON match_assignments
FOR EACH ROW
BEGIN
    DECLARE newDate DATE;
    DECLARE newTime TIME;
    DECLARE t1 INT;
    DECLARE t2 INT;
    DECLARE conflict_count INT DEFAULT 0;
    -- Retrieve the match date, time, and team IDs for the match being assigned
    SELECT date, time_slot, team1_id, team2_id
      INTO newDate, newTime, t1, t2
      FROM matches
     WHERE match_id = NEW.match_id;
    /* Check 1: players are from the correct teams */
    IF NOT EXISTS (SELECT 1 FROM player_teams WHERE username = NEW.white_player AND team_id = t1) THEN
       SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Violation: White player is not a member of the match''s Team1';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM player_teams WHERE username = NEW.black_player AND team_id = t2) THEN
       SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Violation: Black player is not a member of the match''s Team2';
    END IF;
    IF NEW.white_player = NEW.black_player THEN
       SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Violation: The same player cannot play for both teams in a match';
    END IF;
    /* Check 2: white player schedule conflict */
    SELECT COUNT(*) INTO conflict_count
      FROM match_assignments A
      JOIN matches M ON A.match_id = M.match_id
     WHERE (A.white_player = NEW.white_player OR A.black_player = NEW.white_player)
       AND M.date = newDate
       AND ( newTime < ADDTIME(M.time_slot, '02:00:00')
             AND M.time_slot < ADDTIME(newTime, '02:00:00') )
       AND A.match_id <> NEW.match_id;
    IF conflict_count > 0 THEN
       SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Violation: Selected white player is already playing in another match at that time';
    END IF;
    /* Check 3: black player schedule conflict */
    SELECT COUNT(*) INTO conflict_count
      FROM match_assignments A
      JOIN matches M ON A.match_id = M.match_id
     WHERE (A.white_player = NEW.black_player OR A.black_player = NEW.black_player)
       AND M.date = newDate
       AND ( newTime < ADDTIME(M.time_slot, '02:00:00')
             AND M.time_slot < ADDTIME(newTime, '02:00:00') )
       AND A.match_id <> NEW.match_id;
    IF conflict_count > 0 THEN
       SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Violation: Selected black player is already playing in another match at that time';
    END IF;
END$$

DELIMITER $$

-- drop first if the faulty trigger was partially created (it wasn't, but safe anyway)
DROP TRIGGER IF EXISTS trg_player_assignment_check_upd $$

CREATE TRIGGER trg_player_assignment_check_upd
BEFORE UPDATE ON match_assignments
FOR EACH ROW
BEGIN
    /* ---- 1. local variables must be declared first ---- */
    DECLARE newDate   DATE;
    DECLARE newTime   TIME;
    DECLARE team1_id  INT;
    DECLARE team2_id  INT;
    DECLARE conflict  INT DEFAULT 0;

    /* ---- 2. fetch match information ---- */
    SELECT m.date, m.time_slot, m.team1_id, m.team2_id
      INTO newDate, newTime, team1_id, team2_id
      FROM matches AS m
     WHERE m.match_id = NEW.match_id;

    /* ---- 3. Same player for both colours? ---- */
    IF NEW.white_player = NEW.black_player THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT =
              'Violation: The same player cannot play for both teams in a match';
    END IF;

    /* ---- 4. Team–membership checks ---- */
    IF NOT EXISTS (
         SELECT 1 FROM player_teams
          WHERE username = NEW.white_player
            AND team_id  = team1_id
       ) THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT =
              'Violation: White player is not a member of the match''s Team1';
    END IF;

    IF NOT EXISTS (
         SELECT 1 FROM player_teams
          WHERE username = NEW.black_player
            AND team_id  = team2_id
       ) THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT =
              'Violation: Black player is not a member of the match''s Team2';
    END IF;

    /* ---- 5. Overlapping-schedule check for WHITE ---- */
    SELECT COUNT(*)
      INTO conflict
      FROM match_assignments A
      JOIN matches M ON M.match_id = A.match_id
     WHERE (A.white_player = NEW.white_player OR A.black_player = NEW.white_player)
       AND M.date = newDate
       AND ( newTime <  ADDTIME(M.time_slot,'02:00:00')
             AND M.time_slot < ADDTIME(newTime  ,'02:00:00') )
       AND A.match_id <> NEW.match_id;

    IF conflict > 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT =
              'Violation: Selected white player is already playing in another match at that time';
    END IF;

    /* ---- 6. Overlapping-schedule check for BLACK ---- */
    SELECT COUNT(*)
      INTO conflict
      FROM match_assignments A
      JOIN matches M ON M.match_id = A.match_id
     WHERE (A.white_player = NEW.black_player OR A.black_player = NEW.black_player)
       AND M.date = newDate
       AND ( newTime <  ADDTIME(M.time_slot,'02:00:00')
             AND M.time_slot < ADDTIME(newTime  ,'02:00:00') )
       AND A.match_id <> NEW.match_id;

    IF conflict > 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT =
              'Violation: Selected black player is already playing in another match at that time';
    END IF;
END$$

-- Procedure: createMatch(date, time, hall, table, team1, team2, arbiter)
-- Schedules a new match if no conflicts in time/place and teams/arbiter are valid.
DROP PROCEDURE IF EXISTS createMatch $$
CREATE PROCEDURE createMatch(
    IN inMatchDate DATE,
    IN inTime TIME,
    IN inHall INT,
    IN inTable INT,
    IN inTeam1 INT,
    IN inTeam2 INT,
    IN inArbiter VARCHAR(50)
)
BEGIN
    DECLARE newMatchID INT;
    DECLARE conflict_count INT DEFAULT 0;
    -- Ensure the two teams are different
    IF inTeam1 = inTeam2 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Cannot create match: team1 and team2 must be different';
    END IF;
    -- Check hall/table availability: no match at same hall & table overlapping this time
    SELECT COUNT(*) INTO conflict_count
      FROM matches
     WHERE date = inMatchDate
       AND hall_id = inHall
       AND table_id = inTable
       AND (
            inTime < ADDTIME(time_slot, '02:00:00')
            AND time_slot < ADDTIME(inTime, '02:00:00')
           );
    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Cannot create match: The selected hall/table is occupied at that time';
    END IF;
    -- (Optional: ensure arbiter is certified and available. We assume triggers handle scheduling conflicts.)
    IF NOT EXISTS (SELECT 1 FROM arbiters WHERE username = inArbiter) THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Cannot create match: Arbiter username not found';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM arbiter_certifications WHERE username = inArbiter) THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Cannot create match: Arbiter is not certified (no certification listed)';
    END IF;
    -- Generate new match_id (max + 1)
    SELECT COALESCE(MAX(match_id) + 1, 1) INTO newMatchID FROM matches;
    -- Insert the new match (ratings starts as NULL, will be set after match by arbiter)
    INSERT INTO matches(match_id, date, time_slot, hall_id, table_id, team1_id, team2_id, arbiter_username, ratings)
    VALUES(newMatchID, inMatchDate, inTime, inHall, inTable, inTeam1, inTeam2, inArbiter, NULL);
    -- Match successfully created (the triggers will automatically enforce no arbiter conflicts, etc.)
END$$

-- Procedure: assignPlayers(match_id, white_player, black_player)
-- Assigns the two players to the given match, if they belong to the respective teams and no prior assignment exists.
DROP PROCEDURE IF EXISTS assignPlayers $$

CREATE PROCEDURE assignPlayers(
    IN inMatchID   INT,
    IN whitePlayer VARCHAR(50),
    IN blackPlayer VARCHAR(50)
)
BEGIN
    /* declarations first */
    DECLARE t1 INT;
    DECLARE t2 INT;
    DECLARE existing INT DEFAULT 0;

    /* pull match teams */
    SELECT team1_id, team2_id
      INTO t1, t2
      FROM matches
     WHERE match_id = inMatchID;

    IF t1 IS NULL OR t2 IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Cannot assign players: match ID not found';
    END IF;

    /* already assigned? */
    SELECT COUNT(*) INTO existing
      FROM match_assignments
     WHERE match_id = inMatchID;

    IF existing > 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Cannot assign players: players already assigned';
    END IF;

    /* white-player team membership */
    IF NOT EXISTS (
         SELECT 1 FROM player_teams
          WHERE username = whitePlayer
            AND team_id  = t1
       ) THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT =
              'Cannot assign players: white player not in match Team1';
    END IF;

    /* black-player team membership */
    IF NOT EXISTS (
         SELECT 1 FROM player_teams
          WHERE username = blackPlayer
            AND team_id  = t2
       ) THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT =
              'Cannot assign players: black player not in match Team2';
    END IF;

    /* same person for both colours? */
    IF whitePlayer = blackPlayer THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Cannot assign players: same player for both teams';
    END IF;

    /* insert assignment */
    INSERT INTO match_assignments(match_id, white_player, black_player, result)
    VALUES (inMatchID, whitePlayer, blackPlayer, 'draw');
END $$

-- Procedure: deleteMatch(match_id)
-- Deletes the specified match and any associated assignments or ratings.
DROP PROCEDURE IF EXISTS deleteMatch $$
CREATE PROCEDURE deleteMatch(
    IN inMatchID INT
)
BEGIN
    -- Attempt to delete the match; cascades will remove any match_assignments and preserve referential integrity
    DELETE FROM matches WHERE match_id = inMatchID;
    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Delete failed: Match ID not found';
    END IF;
    -- If ROW_COUNT > 0, deletion succeeded. (Cascade will handle match_assignments.)
END$$

-- Procedure: viewHalls()
-- Returns a list of all halls with their name, country, and capacity.
DROP PROCEDURE IF EXISTS viewHalls $$
CREATE PROCEDURE viewHalls()
BEGIN
    SELECT hall_name AS Hall, hall_country AS Country, hall_capacity AS Total_Tables
    FROM halls;
END$$

-- Procedure: viewMatchesByArbiter(arbiter_username)
-- Lists all matches assigned to the given arbiter, with details (date, time, location, teams, rating).
DROP PROCEDURE IF EXISTS viewMatchesByArbiter $$
CREATE PROCEDURE viewMatchesByArbiter(
    IN arbUsername VARCHAR(50)
)
BEGIN
    SELECT m.match_id AS MatchID,
           m.date AS Date,
           m.time_slot AS TimeSlot,
           h.hall_name AS Hall,
           m.table_id AS TableNo,
           t1.team_name AS Team1,
           t2.team_name AS Team2,
           IF(m.ratings IS NULL, 'Not rated', m.ratings) AS Rating
    FROM matches m
    JOIN teams t1 ON m.team1_id = t1.team_id
    JOIN teams t2 ON m.team2_id = t2.team_id
    JOIN halls h ON m.hall_id = h.hall_id
    WHERE m.arbiter_username = arbUsername
    ORDER BY m.date, m.time_slot;
    -- (If no rows are returned, the arbiter has no matches assigned.)
END$$

-- Procedure: submitRating(arb_username, match_id, rating_value)
-- Allows an arbiter to submit a rating for a match after it has occurred (only by assigned arbiter, once).
DROP PROCEDURE IF EXISTS submitRating $$
CREATE PROCEDURE submitRating(
    IN arbUsername VARCHAR(50),
    IN inMatchID INT,
    IN ratingVal DECIMAL(3,1)
)
BEGIN
    DECLARE assignedArb VARCHAR(50);
    DECLARE matchDate DATE;
    DECLARE existingRating DECIMAL(3,1);
    -- Retrieve the match's assigned arbiter, date, and current rating
    SELECT arbiter_username, date, ratings INTO assignedArb, matchDate, existingRating
    FROM matches WHERE match_id = inMatchID;
    IF assignedArb IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'SubmitRating failed: Match ID not found';
    END IF;
    IF assignedArb <> arbUsername THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'SubmitRating failed: Only the assigned arbiter can rate this match';
    END IF;
    IF existingRating IS NOT NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'SubmitRating failed: This match has already been rated';
    END IF;
    IF matchDate >= CURDATE() THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'SubmitRating failed: Match date has not passed yet';
    END IF;
    -- All checks passed: update the match's rating
    UPDATE matches SET ratings = ratingVal WHERE match_id = inMatchID;
    -- (Triggers ensure that once set, the rating cannot be changed.)
END$$

-- Procedure: showMatchStats(arbiter_username)
-- Returns the total number of matches rated by the given arbiter and the average rating given.
DROP PROCEDURE IF EXISTS showMatchStats $$
CREATE PROCEDURE showMatchStats(
    IN paramArb VARCHAR(50)
)
BEGIN
    SELECT
      COUNT(ratings) AS Total_Matches_Rated,
      IF(COUNT(ratings) = 0, 0, ROUND(AVG(ratings), 2)) AS Avg_Rating
    FROM matches
    WHERE arbiter_username = paramArb
      AND ratings IS NOT NULL;
    -- (If Total_Matches_Rated is 0, Avg_Rating is shown as 0.00 for convenience.)
END$$

-- Procedure: showCoPlayerStats(player_username)
-- Returns two result sets: (1) list of all opponents this player has faced, (2) the ELO of the most frequent opponent (or average ELO if tied).
DROP PROCEDURE IF EXISTS showCoPlayerStats $$

CREATE PROCEDURE showCoPlayerStats (IN paramPlayer VARCHAR(50))
BEGIN
    /* ---- declarations must come first ---- */
    DECLARE maxGames INT     DEFAULT 0;
    DECLARE avgElo   DOUBLE;

    /* ---- result set 1: all distinct opponents ---- */
    SELECT DISTINCT
           CASE
               WHEN white_player = paramPlayer THEN black_player
               ELSE white_player
           END AS Opponent
      FROM match_assignments
     WHERE paramPlayer IN (white_player, black_player);

    /* ---- compute the maximum number of games vs. any single opponent ---- */
    SELECT MAX(game_count) INTO maxGames
      FROM (
            SELECT CASE
                     WHEN white_player = paramPlayer THEN black_player
                     ELSE white_player
                   END AS opp,
                   COUNT(*) AS game_count
              FROM match_assignments
             WHERE paramPlayer IN (white_player, black_player)
             GROUP BY opp
           ) AS opp_counts;

    /* ---- if there is at least one game, get average Elo of the most-frequent opponent(s) ---- */
    IF maxGames IS NULL OR maxGames = 0 THEN
        SET avgElo = NULL;          -- player has no opponents
    ELSE
        SELECT AVG(p.elorating) INTO avgElo
          FROM players p
          JOIN (
                  SELECT CASE
                           WHEN white_player = paramPlayer THEN black_player
                           ELSE white_player
                         END AS opp,
                         COUNT(*) AS games
                    FROM match_assignments
                   WHERE paramPlayer IN (white_player, black_player)
                   GROUP BY opp
                  HAVING games = maxGames        -- only the most-frequent opponent(s)
               ) AS most_opp
            ON p.username = most_opp.opp;
    END IF;

    /* ---- result set 2: Elo of the most-frequent opponent (or average if tied) ---- */
    SELECT IF (maxGames = 0 OR avgElo IS NULL,
               'No opponents',
               ROUND(avgElo, 0)) AS Most_Frequent_Opponent_ELO;
END $$
DELIMITER ;

