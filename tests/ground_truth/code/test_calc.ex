# Elixir Test File
defmodule Calculator do
  def add(a, b), do: a + b
  def subtract(a, b), do: a - b
  def multiply(a, b), do: a * b
  def divide(a, b) when b != 0, do: a / b
  def divide(_, 0), do: {:error, "Division durch Null"}
end

defmodule Main do
  def run do
    result = Calculator.add(10, 5)
    IO.puts("Ergebnis: #{result}")
  end
end

Main.run()
