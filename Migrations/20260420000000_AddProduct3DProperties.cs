using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace TH3.Migrations
{
    /// <inheritdoc />
    public partial class AddProduct3DProperties : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "CompatibleDeviceCode",
                table: "Products",
                type: "nvarchar(20)",
                maxLength: 20,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "MaterialType",
                table: "Products",
                type: "nvarchar(40)",
                maxLength: 40,
                nullable: false,
                defaultValue: "Silicone");

            migrationBuilder.AddColumn<string>(
                name: "CaseTexturePath",
                table: "Products",
                type: "nvarchar(500)",
                maxLength: 500,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "Case3DModelPath",
                table: "Products",
                type: "nvarchar(500)",
                maxLength: 500,
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "CompatibleDeviceCode",
                table: "Products");

            migrationBuilder.DropColumn(
                name: "MaterialType",
                table: "Products");

            migrationBuilder.DropColumn(
                name: "CaseTexturePath",
                table: "Products");

            migrationBuilder.DropColumn(
                name: "Case3DModelPath",
                table: "Products");
        }
    }
}
