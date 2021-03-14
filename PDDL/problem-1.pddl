;; Problem definition
(define (problem problem-1)

  ;; Specifying the domain for the problem
  (:domain vaccine-domain)

  ;; Objects definition
  (:objects
    ; Warehouse
    WH1
    WH2
    ; Cities
    C1
    C2
    C3
    ; Hospital
    H1
    H2
    H3
    H4
    ; Vaccines
    V1
    V2
    V3
    V4
    ; Freezing units
    FR1
    ; Vehicles
    LR1
    SR1
    SR2
    SR3
  )

  ;; Intial state of problem 1
  (:init
    ;; Declaration of the objects
    ; We initialize the warehouse
    (WAREHOUSE WH1)
    (WAREHOUSE WH2)
    ; Cities
    (CITY C1)
    (CITY C2)
    (CITY C3)
    ; Hospital
    (HOSPITAL H1)
    (HOSPITAL H2)
    (HOSPITAL H3)
    (HOSPITAL H4)
    ; Vaccines
    (VACCINE V1)
    (VACCINE V2)
    (VACCINE V3)
    (VACCINE V4)
    ; Freezing units
    (FREEZER FR1)
    ; Vehicles
    (VEHICLE LR1)
    (VEHICLE SR1)
    (VEHICLE SR2)
    (VEHICLE SR3)
    (LONG-RANGE-VEHICLE LR1)
    (SHORT-RANGE-VEHICLE SR1)
    (SHORT-RANGE-VEHICLE SR2)
    (SHORT-RANGE-VEHICLE SR3)
    (vehicle-has-freezer SR1)
    (vehicle-has-freezer SR2)
    (vehicle-has-freezer SR3)
    ; Roads
    (connected WH1 C1) (connected C1 WH1)
    (connected WH1 C2) (connected C2 WH1)
    (connected WH2 C3) (connected C3 WH2)
    (connected C1 C3) (connected C3 C1)
    (connected C2 C3) (connected C3 C2)
    (connected C1 H1) (connected H1 C1)
    (connected C1 H2) (connected H2 C1)
    (connected C2 H3) (connected H3 C2)
    (connected C3 H4) (connected H4 C3)
    

    ;; Declaration of the predicates of the objects
    ; We set vehicles locations
    (is-vehicle-at LR1 C1)
    (is-vehicle-at SR1 C1)
    (is-vehicle-at SR2 C2)
    (is-vehicle-at SR3 C3)
    ; We set the vaccines and freezers initial position
    (is-object-at V1 WH1)
    (is-object-at V2 WH1)
    (is-object-at V3 WH2)
    (is-object-at V4 WH2)
    (is-object-at FR1 WH1)
    (is-temperature-sensible V2)
    (is-temperature-sensible V4)
  )

  ;; Goal specification
  (:goal
    (and
      ; We want both vaccines at one hospital (H3)
      (or (is-object-at V1 H1) (is-object-at V2 H1) (is-object-at V3 H1) (is-object-at V4 H1))
      (or (is-object-at V1 H2) (is-object-at V2 H2) (is-object-at V3 H2) (is-object-at V4 H2))
      (or (is-object-at V1 H3) (is-object-at V2 H3) (is-object-at V3 H3) (is-object-at V4 H3))
      (or (is-object-at V1 H4) (is-object-at V2 H4) (is-object-at V3 H4) (is-object-at V4 H4))
    )
  )

)