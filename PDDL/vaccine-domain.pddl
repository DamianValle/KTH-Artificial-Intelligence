;; Domain definition
(define (domain vaccine-domain)
    (:requirements :disjunctive-preconditions :negative-preconditions)

  ;; Predicates: Properties of vaccines that we are interested in (boolean)
  (:predicates
    (WAREHOUSE ?x) ; True if x is a WAREHOUSE
    (CITY ?x) ; True if x is a city
    (HOSPITAL ?x) ; True if x is an hospital
    (VACCINE ?x) ; True if x is a vaccine
    (VEHICLE ?x) ; True if x is a method of transportation
    (FREEZER ?x) ; True if x is a freezing unit
    (LONG-RANGE-VEHICLE ?x) ; True if x is a long-range vehicle
    (SHORT-RANGE-VEHICLE ?x) ; True if x is a short-range vehicle
    (is-temperature-sensible ?x) ; True if x is sensible to temperature changes
    (vehicle-has-freezer ?x) ; True if vehicle x has a freezing unit
    (connected ?x ?y) ; True if x is connected with y (warehouse, city or hospital)
    (is-object-at ?x ?y) ; True if object x (vaccine or freeezer) is at warehouse/city y
    (is-vehicle-at ?x ?y) ; True if vehicle x is at warehouse/city y
    (is-vaccine-in-vehicle ?x ?y) ; True if vaccine x is in vehicle y
  )

  ;; Actions: Ways of changing the state of the world
  
  ; Vaccine x is loaded into vehicle y if both are in the same city/warehouse/hospital z and 
  ; if x is not temperature-sensible or the vehicle already has a freezing unit.
  ; As a result, vaccine x is in vehicle y and not at z anymore.
  ; Parameters
  ; - x: vaccine
  ; - y: vehicle
  ; - z: city or warehouse or hopsital
  (:action load-vaccine
    :parameters (?x ?y ?z)
    :precondition (and 
        (VACCINE ?x) 
        (VEHICLE ?y) 
        (or (CITY ?z) (WAREHOUSE ?z) (HOSPITAL ?z))
        (is-object-at ?x ?z) 
        (is-vehicle-at ?y ?z)
        (or (not (is-temperature-sensible ?x)) (vehicle-has-freezer ?y))
    )
    :effect (and 
        (is-vaccine-in-vehicle ?x ?y)
        (not (is-object-at ?x ?z))
    )
  )
  
  ; Vaccine x is unloaded from vehicle y in city/warehouse z if the vaccine x is in the 
  ; vehicle y and the vehicle y is at z.
  ; As a result, vaccine x is not in vehicle y anymore and the vaccine x is at z
  ; Parameters
  ; - x: vaccine
  ; - y: vehicle
  ; - z: city or warehouse or hospital
  (:action unload-vaccine
    :parameters (?x ?y ?z)
    :precondition (and 
        (VACCINE ?x) 
        (VEHICLE ?y) 
        (or (CITY ?z) (WAREHOUSE ?z) (HOSPITAL ?z))
        (is-vaccine-in-vehicle ?x ?y) 
        (is-vehicle-at ?y ?z)
    )
    :effect (and 
        (not (is-vaccine-in-vehicle ?x ?y))
        (is-object-at ?x ?z)
    )
  )

  ; Freezer x is loaded into vehicle y if both are in the same city/warehouse/hospital z
  ; As a result, freezer x is in vehicle y and not at z anymore.
  ; Parameters
  ; - x: freezing unit
  ; - y: vehicle
  ; - z: city or warehouse or hospital
  (:action load-freezer
    :parameters (?x ?y ?z)
    :precondition (and 
        (FREEZER ?x) 
        (VEHICLE ?y) 
        (or (CITY ?z) (WAREHOUSE ?z) (HOSPITAL ?z))
        (is-object-at ?x ?z) 
        (is-vehicle-at ?y ?z)
    )
    :effect (and 
        (vehicle-has-freezer ?y)
        (not (is-object-at ?x ?z))
    )
  )

  ; Long-distance travel, i.e. between cities or warehouse x and y by a 
  ; long-range vehicle z if x and y are connected.
  ; As a result, vehicle z is at y.
  ; Parameters
  ; - x: city/warehouse from
  ; - y: city/warehouse to
  ; - z: long-range-vehicle
  (:action travel-long
    :parameters (?x ?y ?z)
    :precondition (and 
        (or (CITY ?x) (WAREHOUSE ?x))
        (or (CITY ?y) (WAREHOUSE ?y))
        (LONG-RANGE-VEHICLE ?z)
        (connected ?x ?y) 
        (is-vehicle-at ?z ?x)
        (vehicle-has-freezer ?z)
    )
    :effect (and 
        (is-vehicle-at ?z ?y)
        (not (is-vehicle-at ?z ?x))
    )
  )

  ; Short-distance travel, inside cities, by a 
  ; short-range vehicle z if x and y are connected.
  ; As a result, vehicle z is at y.
  ; Parameters
  ; - x: city or hospital from
  ; - y: hospital or city to
  ; - z: short-range-vehicle
  (:action travel-short
    :parameters (?x ?y ?z)
    :precondition (and 
        (or (CITY ?x) (HOSPITAL ?x))
        (or (CITY ?y) (HOSPITAL ?y))
        (SHORT-RANGE-VEHICLE ?z)
        (connected ?x ?y) 
        (is-vehicle-at ?z ?x)
    )
    :effect (and 
        (is-vehicle-at ?z ?y)
        (not (is-vehicle-at ?z ?x))
    )
  )
  
  
)