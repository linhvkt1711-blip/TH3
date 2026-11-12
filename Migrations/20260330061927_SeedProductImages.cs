using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace TH3.Migrations
{
    /// <inheritdoc />
    public partial class SeedProductImages : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Check if table has any data first
            migrationBuilder.Sql(@"
            -- Get all products and add sample images to them
            IF EXISTS (SELECT 1 FROM Products)
            BEGIN
                DECLARE @ProductId INT;
                DECLARE @ImageIndex INT = 0;
                DECLARE @MaxProductId INT;
                
                SELECT @MaxProductId = MAX(Id) FROM Products;
                
                SET @ProductId = 1;
                
                WHILE @ProductId <= @MaxProductId
                BEGIN
                    IF EXISTS (SELECT 1 FROM Products WHERE Id = @ProductId)
                    BEGIN
                        -- Add 2 sample images to each product
                        INSERT INTO ProductImages (ProductId, Url)
                        VALUES 
                            (@ProductId, '/images/5b093b7f-ff99-4770-887c-6ac47e315e28.jpg'),
                            (@ProductId, '/images/5e036724-f7a7-42b2-96f3-34610d139414.jpg');
                    END
                    
                    SET @ProductId = @ProductId + 1;
                END
            END
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("DELETE FROM ProductImages WHERE Url LIKE '/images/%'");
        }
    }
}
