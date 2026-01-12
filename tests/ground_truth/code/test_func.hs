-- Haskell Test File
module Main where

-- Datentyp Definition
data Person = Person { name :: String, age :: Int }

-- Funktion zur Begrüßung
greet :: Person -> String
greet p = "Hallo, " ++ name p ++ "! Du bist " ++ show (age p) ++ " Jahre alt."

-- Fibonacci
fib :: Int -> Int
fib 0 = 0
fib 1 = 1
fib n = fib (n-1) + fib (n-2)

main :: IO ()
main = do
    let person = Person "Max" 30
    putStrLn \$ greet person
    putStrLn \$ "Fib(10) = " ++ show (fib 10)
