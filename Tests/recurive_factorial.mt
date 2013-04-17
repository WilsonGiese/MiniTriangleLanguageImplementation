! Recursive factotial in Mini-Triangle; Woohoo
let
	func fact(n:Integer):Integer
		if n < 2 then
			return 1; 
		else
			return (n * fact(n - 1)); 
	var result: Integer; 
in 
	begin
		result := fact(getint());
		putint(result);
	end
