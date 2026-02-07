def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        self.iteration += 1
        
        # --- DÉFINITION DES CAPTEURS (Indispensable pour que ton code marche) ---
        sensor_front = 2
        sensor_left = 0
        sensor_right = 4
        
        # Valeurs par défaut (Ta "Promenade")
        translation = 0.9
        rotation = 0.0

        # ====================================================================
        # PRIORITÉ 1 : ÉVITER LES OBSTACLES (SURVIE)
        # ====================================================================
        # Si on détecte un mur, ON S'ARRÊTE LÀ. On ne regarde ni ennemis ni alliés.
        if sensors[sensor_front] < 0.05:
            if sensors[sensor_left] > sensors[sensor_right]:
                rotation = 0.7  # Tourne à gauche
            else:
                rotation = -0.7  # Tourne à droite
            
            # STOP ! On envoie la commande tout de suite pour ne pas s'écraser.
            return translation, rotation, False

        # ====================================================================
        # PRIORITÉ 2 : ÉVITER LES ALLIÉS (NE PAS SE GÊNER)
        # ====================================================================
        # On passe ici seulement si on n'a PAS de mur devant.
        if sensor_view is not None and sensor_team is not None:
            for i in range(8):
                if sensor_view[i] == 2 and sensor_team[i] == self.team_name:
                    # On a trouvé un allié
                    translation = 0.5
                    if i == 0:  # Droit devant (Attention: vérifie si 0 est devant sur ton robot)
                        rotation = 0.0 
                    elif i < 4:  # À droite
                        rotation = 0.5  # S'éloigne
                    else:  # À gauche
                        rotation = -0.5  # S'éloigne
                    
                    # STOP ! On évite le copain, on ignore les ennemis.
                    return translation, rotation, False

        # ====================================================================
        # PRIORITÉ 3 : ATTAQUE (ENNEMI)
        # ====================================================================
        # On passe ici seulement si : Pas de mur ET Pas d'allié.
        if sensor_view is not None and sensor_team is not None:
            for i in range(8):
                if sensor_view[i] == 2 and sensor_team[i] != self.team_name:
                    # ENNEMI DÉTECTÉ ! Charge !
                    translation = 1.0
                    if i == 0:  # Droit devant
                        rotation = 0.0
                    elif i < 4:  # À droite
                        rotation = -0.3
                    else:  # À gauche
                        rotation = 0.3
                    
                    # STOP ! On fonce sur l'ennemi.
                    return translation, rotation, False

        # ====================================================================
        # PRIORITÉ 4 : VARIATION ALÉATOIRE (SI RIEN D'AUTRE)
        # ====================================================================
        # Si on arrive ici, c'est que la voie est libre.
        if self.iteration % 60 == 0:
            rotation += 0.3 if (self.iteration // 60) % 2 == 0 else -0.3

        return translation, rotation, False