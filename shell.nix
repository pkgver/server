{ pkgs ? import <nixpkgs> { } }:

let
  packages = with pkgs.python3Packages; [
    fastapi
    uvicorn
    GitPython
  ];
in
pkgs.mkShell {
  buildInputs = [ pkgs.python3Full ] ++ packages;
}
