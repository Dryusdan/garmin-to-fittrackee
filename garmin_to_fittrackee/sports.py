from garmin_to_fittrackee.logs import Log

log = Log(__name__)


class Sports:
    @staticmethod
    def get_fittrackee_sport_by_garmin_id(garmin_sport_id: int) -> int:
        if not isinstance(garmin_sport_id, int):
            log.critical(f"garmin_sport_id {garmin_sport_id} is not an int")
            raise ValueError(f"garmin_sport_id {garmin_sport_id} is not an int")
        match garmin_sport_id:
            # Bike cases
            case 2 | 10 | 21 | 22 | 197:
                """
                2 reference cycle
                10 reference road_cycle
                21 reference track_cycling
                22 reference recumbent_cycling
                197 reference hand_cycling
                """
                log.debug(f"Road cycling match with garmin sport id {garmin_sport_id}")
                return 1
            case 5 | 19 | 20 | 143:
                """
                5 reference mountain_biking
                19 reference cyclocross
                20 reference downhill_biking
                143 reference gravel_cycling
                """
                log.debug(f"Mountain bike match with garmin sport id {garmin_sport_id}")
                return 4
            case 175:
                """
                175 reference e_bike_mountain
                """
                log.debug(
                    f"E-Mountain bike match with garmin sport id {garmin_sport_id}"
                )
                return 7
            case 25 | 152 | 176 | 198:
                """
                25 reference indoor_cycling
                152 reference virtual_ride
                176 reference e_bike_fitness
                198 reference indoor_hand_cycling
                """
                log.debug(
                    f"Virtual cycling match with garmin sport id {garmin_sport_id}"
                )
                return 13
            # Running cases
            case 1 | 7 | 8 | 18 | 153 | 154 | 156 | 181:
                """
                1 reference running
                7 reference street_running
                8 reference track_running
                18 reference treadmill_running
                153 reference virtual_run
                154 reference obstacle_run
                156 reference indoor_running
                181 reference ultra_run
                """
                log.debug(f"Running match with garmin sport id {garmin_sport_id}")
                return 5
            # Hiking cases
            case 3:
                log.debug(f"Hiking match with garmin sport id {garmin_sport_id}")
                return 3
            # Walking case
            case 9 | 15 | 16:
                """
                9 reference walking
                15 reference casual_walking
                16 reference speed_walking
                """
                log.debug(f"Walking match with garmin sport id {garmin_sport_id}")
                return 6
            # Winter sport cases
            case 167:
                """
                167 reference snow_shoe_ws
                """
                log.debug(f"Snowshoes match with garmin sport id {garmin_sport_id}")
                return 12
            case 172 | 251 | 252:
                """
                172 reference resort_skiing_snowboarding_ws
                251 reference resort_skiing
                252 reference resort_snowboarding
                """
                log.debug(
                    f"Skiing (Alpine) match with garmin sport id {garmin_sport_id}"
                )
                return 9
            case 168 | 169 | 170 | 171 | 203 | 204:
                """
                168 reference skating_ws
                169 reference backcountry_skiing_snowboarding_ws
                170 reference skate_skiing_ws
                171 reference cross_country_skiing_ws
                203 reference backcountry_skiing
                204 reference backcountry_snowboarding
                """
                log.debug(
                    "Skiing (Cross Country) match"
                    "with garmin sport id {garmin_sport_id}"
                )
                return 10
            # Mountaineering case
            case 37:
                log.debug(
                    f"Mountaineering match with garmin sport id {garmin_sport_id}"
                )
                return 14
            # Open Water swimming case
            case 28:
                log.debug(
                    f"Open Water Swimming match with garmin sport id {garmin_sport_id}"
                )
                return 16
            # Trail case
            case 6:
                log.debug(f"Trail match with garmin sport id {garmin_sport_id}")
                return 8
            # Rowing case
            case 32 | 237:
                """
                32 reference indoor_rowing
                237 reference rowing_v2
                """
                log.debug(f"Rowing match with garmin sport id {garmin_sport_id}")
                return 11
            case _:
                log.error(
                    f"Not Fittrackee match with garmin sport id {garmin_sport_id}"
                )
                log.error("Set to cycling road")
                return 1
