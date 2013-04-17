! Should print 15 then # you enter then 8 then 5 then -5
! Demonstrates scoping, precedence, function definitions,
! semicolons as terminators, and function calls as expressions 
let
    const m ~ 3;
    const l ~ 2;
    func foo(x: Integer, y: Integer): Integer
        begin
            x := x + y;
            return x;
        end
    func foo2(x: Integer): Integer
        begin
            x := -x;
            putint(x);
            return x;
        end
    var n: Integer;
in
    begin
        let
            const a ~ 3;
            const b ~ 4;
            var c: Integer;
        in
            begin
                c := a * b + 12 / b;
                putint(c);
                c := getint();
                putint(c); 
            end
        n := 2 + m * m - 6 / l;
        putint(n);
        n := foo(m, l);
        putint(n);
        foo2(n);
    end