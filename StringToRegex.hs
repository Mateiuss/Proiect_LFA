{-# OPTIONS_GHC -Wno-deferred-out-of-scope-variables #-}
{-# OPTIONS_GHC -Wno-incomplete-patterns #-}
module StringToRegex where
import Regex_NFA ( Regex (Simple, Vid, UNION, CONCAT, STAR, Epsilon, Miss), mysplit, extractChar, regex_read )
import Data.List (isPrefixOf, insert)
import System.FilePath (combine)
import Debug.Trace (trace)

reverseRegex :: Regex -> Regex
reverseRegex (Simple c) = Simple c
reverseRegex Vid = Vid
reverseRegex Miss = Miss
reverseRegex Epsilon = Epsilon
reverseRegex (STAR r) = STAR $ reverseRegex r
reverseRegex (CONCAT a b) = CONCAT (reverseRegex b) (reverseRegex a)
reverseRegex (UNION a b) = UNION (reverseRegex b) (reverseRegex a)

-- TODO include Special characters in the string
-- ignore first and last '\''
obtainCharacter :: String -> (Char, Int)
obtainCharacter str
    -- TODO: add other special chars
    | "'\\n'" `isPrefixOf` str = ('\n', 4)
    | head str == '\'' = (str !! 1, 3)
    | otherwise  = (head str, 1)


combineReg :: Regex -> Regex
combineReg (CONCAT Epsilon Epsilon) = Epsilon
combineReg (CONCAT Epsilon a) = a
combineReg (CONCAT a Epsilon) = a
combineReg (CONCAT a b) = CONCAT a b

missing :: Regex -> Bool
missing (Simple _) = False
missing Epsilon = True
missing (STAR e) = missing e
missing (CONCAT a b) = missing a || missing b
missing (UNION a b) = missing a || missing b
missing Miss = True

minimizeStack :: [Regex] -> [Regex]
minimizeStack (x:xs) = minStack x xs

minimizeStackRecursive :: [Regex] -> [Regex]
minimizeStackRecursive (x:xs) = minStackRecursive x xs

-- Cand am ), minimizes stackul pana la primul Miss sau CONCAT Miss Miss
minStack :: Regex -> [Regex] -> [Regex]
minStack e [] = [e]
minStack e (r:regs)
    | r == Miss = e : regs        
    | r == CONCAT Miss Miss = e : regs
    | not (missing r) = r:regs
    | otherwise = minStack (insertRegMiss e r) regs

minStackRecursive :: Regex -> [Regex] -> [Regex]
minStackRecursive e [] = [e]
minStackRecursive e (r:regs)
    | not (missing r) = [Vid]
    | regs /= [] = minStackRecursive n regs
    | regs == [] && missing n = [n]
    | otherwise  = [n]
        where n = insertRegMiss e r

insertRegMiss :: Regex -> Regex -> Regex
insertRegMiss a Epsilon = a
insertRegMiss Epsilon e = e
insertRegMiss a Miss = a
insertRegMiss a (CONCAT b Miss) = CONCAT b a
insertRegMiss a (CONCAT b c)
    | missing c = CONCAT b (insertRegMiss a c)
    | missing b = CONCAT (insertRegMiss a b) c
    | otherwise = CONCAT b c
insertRegMiss a (UNION b Miss) = UNION b a
insertRegMiss a (UNION b c)
    | missing c = UNION b (insertRegMiss a c)
    | missing b = UNION (insertRegMiss a b) c
    | otherwise = UNION b c
insertRegMiss a (STAR Miss) = STAR a
insertRegMiss a (STAR b) = STAR $ insertRegMiss a b

parse :: (String, [Regex]) -> (String, [Regex])
parse (str, stack@(x:xs))
    | str == "" = ("GATA", minStackRecursive x xs)
    | head str == ' ' = parse (tail str, stack) -- ignore empty spaces
    | head str == '*' = parse (drop len str, STAR x:xs)
    | head str == '+' = parse (drop len str, (CONCAT (STAR x) x):xs)
    | head str == '(' = 
        if x /= Epsilon then
            parse (tail str, Miss:CONCAT Miss x:xs)
        else
            parse (tail str, Miss:xs)
    | head str == ')' = parse (tail str, minimizeStack stack)
    | head str == '|' = parse (tail str, Epsilon:UNION Miss x:xs)
    | "[a-z]+" `isPrefixOf` str && x /= Epsilon = parse (drop 6 str, lettersPlus:(CONCAT Miss x:xs))
    | "[a-z]+" `isPrefixOf` str && x == Epsilon = parse (drop 6 str, lettersPlus:xs)
    | "[0-9]+" `isPrefixOf` str && x /= Epsilon = parse (drop 6 str, numbersPlus:(CONCAT Miss x:xs))
    | "[0-9]+" `isPrefixOf` str && x == Epsilon = parse (drop 6 str, numbersPlus:xs)
    | len /= -1 && x /= Epsilon = parse (drop len str, Simple ch:(CONCAT Miss x:xs))
    | len /= -1 && x == Epsilon = parse (drop len str, Simple ch:xs)
        where (ch, len) = obtainCharacter str

parseRegex :: String -> Regex
parseRegex str = reverseRegex $ head reg
    where (str_left, reg) = parse (str, [Epsilon])

letters :: Regex
letters = foldl (\ reg ch -> UNION (Simple ch) reg) (Simple 'a') ['b'..'s']
lettersPlus :: Regex
lettersPlus = CONCAT (STAR letters) letters
numbers :: Regex
numbers = foldl (\ reg ch -> UNION (Simple ch) reg) (Simple '0') ['1'..'9']
numbersPlus :: Regex
numbersPlus = CONCAT numbers $ STAR numbers