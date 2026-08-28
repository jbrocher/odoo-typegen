{
  inputs = {
    utils.url = "github:numtide/flake-utils";
  };
  outputs =
    {
      self,
      nixpkgs,
      utils,
    }:
    utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python313;
        pythonPackages = pkgs.python313Packages;
        poetry = pkgs.poetry.override { python3 = python; };
        project = pkgs.lib.importTOML ./pyproject.toml;
        odoo-typegen = pythonPackages.buildPythonApplication {
          pname = project.project.name;
          inherit (project.project) version;
          pyproject = true;
          src = self;

          build-system = [
            pythonPackages.poetry-core
          ];

          dependencies = [
            pythonPackages.astroid
            pythonPackages.cyclopts
            pythonPackages.pydantic
          ];
        };
      in
      {
        packages.default = odoo-typegen;
        packages.odoo-typegen = odoo-typegen;

        apps.default = {
          type = "app";
          program = "${odoo-typegen}/bin/odoo-typegen";
        };

        devShell = pkgs.mkShell rec {
          buildInputs = [
            python
            poetry
            pkgs.nodejs
            odoo-typegen
          ];
          shellHook = ''
            SOURCE_DATE_EPOCH=$(date +%s)
            echo "Activating poetry env..."
            eval "$(poetry env activate)"

            venvDir=$(poetry env info -p)

            # Under some circumstances it might be necessary to add your virtual
            # environment to PYTHONPATH, which you can do here too;
            PYTHONPATH=$PWD/$venvDir/${pythonPackages.python.sitePackages}/:$PYTHONPATH
          '';
        };
      }
    );
}
