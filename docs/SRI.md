# **The Strategic Representativeness Index (SRI)**


## **1. Motivation: Setting a Smarter Target**

The **Strategic Representativeness Index (SRI)** provides a single, survey-level score that measures how well our sample is composed to deliver maximally *informative* results.

It operates on a simple but powerful principle: the best sample isn't a perfect demographic mirror of the population, but one that is strategically balanced to reduce uncertainty across all groups. It does this by moving away from a purely proportional target and setting a new "ideal" composition that moderately over-samples smaller groups and under-samples larger ones.

This approach directly combats the "diminishing returns" of over-sampling large populations while ensuring the "signal" from smaller populations is stable and reliable.


## **2. The SRI Formula**

The SRI calculates the distance between your actual sample and the ideal strategic target sample.

SRI=1−21​i∑​∣si​−si∗​∣

Where:



* sᵢ = The **actual proportion** of your sample that belongs to stratum i.
* s^*ᵢ = The **ideal strategic target proportion** for stratum i.


### **The Strategic Target (s^*ᵢ)**

The ideal target proportion for each group is calculated by taking the square root of its true population proportion, then normalizing across all groups. This is the mathematical solution to minimizing total weighted uncertainty.

si∗​=∑j​πj​​πi​​​

Where:



* πᵢ = The **true population proportion** for stratum i.


## **3. How It Works**



1. **Redefine the Goal:** The SRI's key innovation is redefining the "perfect" sample. Instead of aiming for sᵢ = πᵢ, the goal becomes sᵢ = s^*ᵢ.
2. **Balance Information:** The square root formula (√πᵢ) still allocates more participants to larger populations, but not at a 1-to-1 rate. This inherently boosts the proportional representation target for smaller countries and tempers it for larger ones, ensuring a more balanced level of statistical power across all groups.
3. **Measure the Gap:** The SRI then simply measures how close your sample's composition came to achieving this new, more intelligent target.


## **4. How to Use with Global Dialogues Data**

To calculate the SRI for a Global Dialogues survey:



1. **Define Strata and Get Population Proportions (πᵢ):** Load your benchmark population data.
2. **Calculate Strategic Targets (s^*ᵢ):** Apply the square root formula to the population proportions to determine the ideal share for each stratum.
3. **Calculate Actual Sample Proportions (sᵢ):** Using your survey data (e.g., GD3_participants.csv), calculate the proportion of your sample belonging to each stratum.
4. **Calculate the SRI Score:** Insert your actual (sᵢ) and target (s^*ᵢ) proportions into the main SRI formula.

The result is a single, stable score that evaluates the overall informative quality of your sample's demographic design.
