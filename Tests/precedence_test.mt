let
	var x: Integer; 
in 
	begin 
		! Expecting 7
		x := 1 + 2 * 3; 
		putint(x); 

		! Expecting 80
		x := 5 + 5 * 5 * (1 + 2);
		putint(x);

		! Expecting 12
		x := (1 + 2 + 3) * 2; 
		putint(x);

		! Expecting 0
		if 6 + 7 * 2 > 2 + 7 * 6 then 
			putint(1);
		else
			putint(0);
	end

