
.. _inverter_faults:

######
Faults
######

There is a total of four OIDs that make up a 128 bit wide field, with each bit representing a particular fault. Each of
the OIDs contains 32 bits. If no bits are set (i.e. the four OIDs return 0), no fault is present.

================ ==============
``fault[0].flt`` Bits 0 to 31
``fault[1].flt`` Bits 32 to 63
``fault[2].flt`` Bits 64 to 95
``fault[3].flt`` Bots 96 to 127
================ ==============

The table lists known faults, if the bit is set in the devices output then the fault is currently present:

=== =========================================================================================
Bit Description
=== =========================================================================================
0   TRAP occured
1   RTC can't be configured
2   RTC 1Hz signal timeout
3   Hardware Stop by 3.3V fault
4   Hardware Stop by PWM Logic
5   Hardware Stop by ``Uzk`` overvoltage
6   ``Uzk+`` is above limit
7   ``Uzk-`` is above limit
8   Throttle phase ``L1`` overcurrent
9   Throttle phase ``L2`` overcurrent
10  Throttle phase ``L3`` overcurrent
11  Buffer capacitor voltage
12  Quartz fault
13  Grid under-voltage phase 1
14  Grid under-voltage phase 2
15  Grid under-voltage phase 3
16  Battery overcurrent
17  Relais test failed
18  Board overtemperature
19  Core overtemperature
20  (Heat)Sink 1 overtemperature
21  (Heat)Sink 2 overtemperature
22  Error in I2C communication with Power Board
23  Power Board error
24  PWM output ports defective
25  Insulation to small or not plausible
26  ``I`` DC component max (1A)
27  ``I`` DC component max slow (47mA)
28  Possible defect in one of the DSD channels (current offset too large)
29  Error in RS485 communication with Relais Box IGBT L1 BH defective
30  Phase to phase overvoltage
31  IGBT L1 BH defective
32  IGBT L1 BL defective
33  IGBT L2 BH defective
34  IGBT L2 BL defective
35  IGBT L3 BH defective
36  IGBT L3 BL defective
37  Long-term overvoltage phase 1
38  Long-term overvoltage phase 2
39  Long-term overvoltage phase 3
40  Overvoltage phase 1, level 1
41  Overvoltage phase 1, level 2
42  Overvoltage phase 2, level 1
43  Overvoltage phase 2, level 2
44  Overvoltage phase 3, level 1
45  Overvoltage phase 3, level 2
46  Overfrequency, level 1
47  Overfrequency, level 2
48  Undervoltage phase 1, level 1
49  Undervoltage phase 1, level 2
50  Undervoltage phase 2, level 1
51  Undervoltage phase 2, level 2
52  Undervoltage phase 3, level 1
53  Undervoltage phase 3, level 2
54  Underfrequency, level 1
55  Underfrequency, level 2
56  CPU exception NMI
57  CPU exception HardFault
58  CPU exception MemManage
59  CPU exception BusFault
60  CPU exception UsageFault
61  RTC Power on reset
62  RTC Oscillation stops
63  RTC Supply voltage drop
64  Jump of RCD current ``DC + AC > 30mA`` was noticed
65  Jump of RCD current ``DC > 60mA`` was noticed
66  Jump of RCD current ``AC > 150mA`` was noticed
67  RCD current ``> 300mA`` was notices
68  Incorrect ``+5V`` was noticed
69  Incorrect ``-9V`` was noticed
70  Incorrect ``+9V`` was noticed
71  Incorrect ``+3V3`` was noticed
72  Failure of RDC calibration was noticed
73  Failure of I2C was noticed
74  afi frequency generator failure
75  (Heat)sink temperature too high
76  ``Uzk`` is over limit
77  ``Usg A`` is over limit
78  ``Usg B`` is over limit
79  Switching On Conditions ``Umin`` phase 1
80  Switching On Conditions ``Umax`` phase 1
81  Switching On Conditions ``Fmin`` phase 1
82  Switching On Conditions ``Fmax`` phase 1
83  Switching On Conditions ``Umin`` phase 2
84  Switching On Conditions ``Umax`` phase 2
85  Battery current sensor defective
86  Battery booster damaged
87  Switching On Conditions ``Umin`` phase 3
88  Switching On Conditions ``Umax`` phase 3
89  Voltage surge or average offset is too large on AC-terminals (phase failure detected)
90  Inverter is disconnected from the household grid
91  Difference of the measured ``+9V`` between DSP and PIC is too large
92  ``1.5V`` error
93  ``2.5V`` error
94  ``1.5V`` measurement difference
95  ``2.5V`` measurement difference
96  The battery voltage is outside of the expected range
97  Unable to start the main PIC software
98  PIC bootloader detected unexpectedly
99  Phase position error (not 120° as expected)
100 Battery overvoltage
101 Throttle current is unstable
102 Difference between internally and externally measured grid voltage is too large in phase 1
103 Difference between internally and externally measured grid voltage is too large in phase 2
104 Difference between internally and externally measured grid voltage is too large in phase 3
105 External emergency turn-off signal is active
106 Battery is empty, not enough energy for standby
107 CAN communication timeout with battery
108 Timing problem
109 Battery IGBT's heat sink overtemperature
110 Battery heat sink temperature too high
111 Internal relais box error
112 Relais box PE off error
113 Relais box PE on error
114 Internal battery error
115 Parameter changed
116 3 attempts of island building are failing
117 Phase to phase undervoltage
118 System reset detected
119 Update detected
120 FRT overvoltage
121 FRT undervoltage
122 IGBT L1 free-wheeling diode defective
123 IGBT L2 free-wheeling diode defective
124 IGBT L3 free-wheeling diode defective
125 Single-phase mode is activated but not allowed for this device class (e.g. 10K)
126 Island detected
=== =========================================================================================

.. 127 is missing from list, possibly not implemented?
