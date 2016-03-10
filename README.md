# enerdata-predictions
Predict future enerdata from a past scenario

## Iteration 0

Get measurements from a CSV file and predict the amount of energy needed for a future date using as a reference the past year events.


## Example of use

```
/usr/bin/python2.7 range.py


Start parsing incoming file lectures.txt
   Takes 19.46158s for 100 registries

Start prediction for all Past CUPS bewteen 2016/12/29 - 2016/12/31
   Takes 0.08047s for 100 registries

Predicted TOTAL consumption of 824 kw between 2016/12/29 - 2016/12/31 based on the last year info

Applying correctional factors
 - 'Set 15% contingency margin' (increase_percent: 15)
    - Result: Total 947.6 kw  (previous 824.0 kw)
   Takes 0.00004s


PREDICTION SUMMARY 

   947.6 kw from 2016/12/29 to 2016/12/31 [2 days]

   + 489.9 kw 2016/12/29
      - 00:00 - 01:00	26.45 kw
      - 01:00 - 02:00	14.95 kw
      - 02:00 - 03:00	11.5 kw
      - 03:00 - 04:00	12.65 kw
      - 04:00 - 05:00	14.95 kw
      - 05:00 - 06:00	13.8 kw
      - 06:00 - 07:00	9.2 kw
      - 07:00 - 08:00	10.35 kw
      - 08:00 - 09:00	19.55 kw
      - 09:00 - 10:00	17.25 kw
      - 10:00 - 11:00	19.55 kw
      - 11:00 - 12:00	26.45 kw
      - 12:00 - 13:00	26.45 kw
      - 13:00 - 14:00	23.0 kw
      - 14:00 - 15:00	24.15 kw
      - 15:00 - 16:00	20.7 kw
      - 16:00 - 17:00	25.3 kw
      - 17:00 - 18:00	20.7 kw
      - 18:00 - 19:00	21.85 kw
      - 19:00 - 20:00	21.85 kw
      - 20:00 - 21:00	31.05 kw
      - 21:00 - 22:00	24.15 kw
      - 22:00 - 23:00	31.05 kw
      - 23:00 - 24:00	23.0 kw

   + 457.7 kw 2016/12/30
      - 00:00 - 01:00	19.55 kw
      - 01:00 - 02:00	14.95 kw
      - 02:00 - 03:00	23.0 kw
      - 03:00 - 04:00	13.8 kw
      - 04:00 - 05:00	9.2 kw
      - 05:00 - 06:00	6.9 kw
      - 06:00 - 07:00	14.95 kw
      - 07:00 - 08:00	14.95 kw
      - 08:00 - 09:00	12.65 kw
      - 09:00 - 10:00	11.5 kw
      - 10:00 - 11:00	17.25 kw
      - 11:00 - 12:00	21.85 kw
      - 12:00 - 13:00	23.0 kw
      - 13:00 - 14:00	26.45 kw
      - 14:00 - 15:00	13.8 kw
      - 15:00 - 16:00	21.85 kw
      - 16:00 - 17:00	18.4 kw
      - 17:00 - 18:00	23.0 kw
      - 18:00 - 19:00	24.15 kw
      - 19:00 - 20:00	19.55 kw
      - 20:00 - 21:00	26.45 kw
      - 21:00 - 22:00	20.7 kw
      - 22:00 - 23:00	29.9 kw
      - 23:00 - 24:00	29.9 kw

   // Applied Margins of '0.15%' and '0%' global

```

## Screenshots

![Prediction1](https://github.com/gisce/enerdata-predictions/blob/master/README/ex1.png)

![Prediction2](https://github.com/gisce/enerdata-predictions/blob/master/README/ex2.png)
