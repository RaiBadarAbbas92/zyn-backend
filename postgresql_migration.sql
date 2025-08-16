-- PostgreSQL Migration Script for Guest Orders Support
-- This script modifies the orders table to allow NULL values in user_id column

-- Check if the column constraint exists and drop it
DO $$
BEGIN
    -- Check if the NOT NULL constraint exists on user_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'orders' 
        AND column_name = 'user_id' 
        AND is_nullable = 'NO'
    ) THEN
        -- Alter the column to allow NULL values
        ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;
        RAISE NOTICE 'Successfully modified user_id column to allow NULL values';
    ELSE
        RAISE NOTICE 'user_id column already allows NULL values';
    END IF;
END $$;

-- Verify the change
SELECT 
    column_name, 
    is_nullable, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'orders' 
AND column_name = 'user_id';
