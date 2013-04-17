let 
	func foo(a:Integer, b:Integer):Integer
		let
			var bool: Integer; 
		in
			begin 
				if a > b then
					bool := 1; 
				else
					bool := 0; 
				return bool;
			end
in 
	! Should print 1, 1, 0, 1, 0
	begin 
		putint(foo(10, 5));
		putint(foo(1993, 193)); 
		putint(foo(50, 100)); 
		putint(foo(2, 1)); 
		putint(foo(88, 89)); 
	end

