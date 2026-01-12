# R Test File
# Datenanalyse Beispiel

library(ggplot2)
library(dplyr)

# Daten erstellen
data <- data.frame(
  name = c("Anna", "Ben", "Clara"),
  age = c(25, 30, 28),
  salary = c(50000, 65000, 55000)
)

# Analyse
summary(data)
avg_salary <- mean(data\)
print(paste("Durchschnittsgehalt:", avg_salary, "EUR"))

# Plot erstellen
ggplot(data, aes(x=name, y=salary)) +
  geom_bar(stat="identity", fill="steelblue") +
  theme_minimal()
