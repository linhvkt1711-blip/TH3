using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace TH3.Migrations
{
    /// <inheritdoc />
    public partial class AddUserPreferences : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "UserPreferences",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    UserId = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    PreferredStyle = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    PreferredMaterial = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    PreferredPriceTier = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: false),
                    PreferredPurpose = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "datetime2", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserPreferences", x => x.Id);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "UserPreferences");
        }
    }
}
