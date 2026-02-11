def wall_follow_left(self, sensors, sensor_view):
    def wall(i):
        return sensor_view[i] == VIEW_WALL

    # distances utiles
    f = sensors[F]
    fl = sensors[FL]
    l = sensors[L]
    rl = sensors[RL]

    # Est-ce qu'on "voit" un mur à gauche (on ignore les robots)
    left_seen = wall(L) or wall(FL) or wall(RL)

    # 1) Mur devant -> s'écarter doucement à droite, MAIS en avançant fort
    if wall(F) and f < 0.55:
        return 0.80, -0.18

    # 2) Si mur à gauche -> garder une distance cible avec correction très faible
    if left_seen:
        if wall(L):
            d = l
        elif wall(FL):
            d = fl
        else:
            d = rl

        target = 0.30
        err = target - d

        # correction ultra douce => pas de spin
        r = max(-0.18, min(0.18, 0.9 * err))  # gain faible, clamp faible

        # avancer toujours (sinon il “accroche” et tourne)
        t = 0.85

        # si vraiment trop proche du mur, on s’écarte un peu plus (toujours soft)
        if d < 0.16:
            r = -0.18
            t = 0.80

        return t, r

    # 3) Pas de mur à gauche -> arc TRÈS large à gauche (capture), pas de virage serré
    return 0.85, +0.12


def hunter(self, sensors, sensor_view, sensor_robot, sensor_team):
    # --- anti-corner (coins) ---
    front_wall = (sensor_view[F] == VIEW_WALL and sensors[F] < 0.55)
    fl_wall = (sensor_view[FL] == VIEW_WALL and sensors[FL] < 0.35)
    fr_wall = (sensor_view[FR] == VIEW_WALL and sensors[FR] < 0.35)

    if front_wall and (fl_wall or fr_wall):
        # reculer + tourner pour se décrocher
        if fl_wall and not fr_wall:
            return -0.35, -0.35  # droite (r négatif)
        if fr_wall and not fl_wall:
            return -0.35, +0.35  # gauche (r positif)
        return -0.35, (+0.35 if self.idx % 2 == 0 else -0.35)

    # --- anti-mur EARLY (à haute vitesse) ---
    if sensor_view[F] == VIEW_WALL and sensors[F] < 0.75:
        # tourne vers le côté le plus libre
        left_free = sensors[FL] if sensor_view[FL] != VIEW_WALL else 0.0
        right_free = sensors[FR] if sensor_view[FR] != VIEW_WALL else 0.0

        t = 0.80
        # ✅ convention: r négatif = droite, r positif = gauche
        r = -0.18 if right_free > left_free else +0.18
        return t, r

    # --- chercher ennemi ---
    best_i = None
    best_d = 1.0
    for i in range(8):
        if is_enemy(sensor_view[i], sensor_team[i], self.team):
            if sensors[i] < best_d:
                best_d = sensors[i]
                best_i = i

    if best_i is not None:
        r = STEER.get(best_i, 0.0)
        if best_d > 0.45:
            t = 0.85
        elif best_d > 0.25:
            t = 0.70
        else:
            t = 0.45
        return clamp(t), clamp(r)

    # --- exploration rapide ---
    t = 0.95
    r = +0.08 if (self.idx % 2 == 0) else -0.08

    # éviter coller aux murs latéraux
    if sensor_view[L] == VIEW_WALL and sensors[L] < 0.28:
        r = -0.16
    elif sensor_view[R] == VIEW_WALL and sensors[R] < 0.28:
        r = +0.16

    # diagonales (pré-évite)
    if sensor_view[FL] == VIEW_WALL and sensors[FL] < 0.35:
        r = -0.16
    if sensor_view[FR] == VIEW_WALL and sensors[FR] < 0.35:
        r = +0.16

    # couloir étroit : ralentir un peu
    if (sensor_view[L] == VIEW_WALL and sensors[L] < 0.22) and (sensor_view[R] == VIEW_WALL and sensors[R] < 0.22):
        t = 0.80

    return clamp(t), clamp(r)