import os
from datetime import datetime, timedelta
from decimal import Decimal
from werkzeug.security import generate_password_hash
from backend.database import engine, Base, SessionLocal
from backend.models import (
    Customer, Address, Category, Product, Cart, CartItem,
    Order, OrderItem, Payment, Delivery, Return, Refund, Review, AuditLog
)

def init_database():
    """Create all tables and seed complete realistic data if not present."""
    print("[Database] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        # Check if already seeded
        if session.query(Product).count() >= 50:
            print("[Database] Database already populated with >= 50 products.")
            return

        print("[Database] Seeding initial mock data...")

        # 1. Customers
        pwd_hash = generate_password_hash("password123")
        customers_data = [
            Customer(
                customer_id="CUS1001",
                name="Rahul Sharma",
                email="rahul@example.com",
                phone="+91 9876543210",
                password_hash=pwd_hash,
                account_status="ACTIVE",
                created_at=datetime.utcnow() - timedelta(days=90)
            ),
            Customer(
                customer_id="CUS1002",
                name="Priya Patel",
                email="priya@example.com",
                phone="+91 9876543211",
                password_hash=pwd_hash,
                account_status="ACTIVE",
                created_at=datetime.utcnow() - timedelta(days=75)
            ),
            Customer(
                customer_id="CUS1003",
                name="Amit Verma",
                email="amit@example.com",
                phone="+91 9876543212",
                password_hash=pwd_hash,
                account_status="ACTIVE",
                created_at=datetime.utcnow() - timedelta(days=60)
            ),
            Customer(
                customer_id="CUS1004",
                name="Sneha Reddy",
                email="sneha@example.com",
                phone="+91 9876543213",
                password_hash=pwd_hash,
                account_status="ACTIVE",
                created_at=datetime.utcnow() - timedelta(days=45)
            ),
            Customer(
                customer_id="CUS1005",
                name="Vikram Singh",
                email="vikram@example.com",
                phone="+91 9876543214",
                password_hash=pwd_hash,
                account_status="ACTIVE",
                created_at=datetime.utcnow() - timedelta(days=30)
            )
        ]
        session.add_all(customers_data)
        session.flush()

        # 2. Addresses
        addresses_data = [
            Address(
                address_id="ADDR1001",
                customer_id="CUS1001",
                full_name="Rahul Sharma",
                phone="+91 9876543210",
                address_line="Flat 402, Sunshine Heights, MG Road",
                city="Bengaluru",
                state="Karnataka",
                postal_code="560001",
                address_type="Home",
                is_default=True
            ),
            Address(
                address_id="ADDR1002",
                customer_id="CUS1001",
                full_name="Rahul Sharma (Office)",
                phone="+91 9876543210",
                address_line="Tower B, 7th Floor, EcoSpace Tech Park, Outer Ring Rd",
                city="Bengaluru",
                state="Karnataka",
                postal_code="560103",
                address_type="Work",
                is_default=False
            ),
            Address(
                address_id="ADDR1003",
                customer_id="CUS1002",
                full_name="Priya Patel",
                phone="+91 9876543211",
                address_line="12-B, Shanti Niketan Society, Navrangpura",
                city="Ahmedabad",
                state="Gujarat",
                postal_code="380009",
                address_type="Home",
                is_default=True
            ),
            Address(
                address_id="ADDR1004",
                customer_id="CUS1003",
                full_name="Amit Verma",
                phone="+91 9876543212",
                address_line="C-44, Sector 62, Near City Center",
                city="Noida",
                state="Uttar Pradesh",
                postal_code="201301",
                address_type="Home",
                is_default=True
            ),
            Address(
                address_id="ADDR1005",
                customer_id="CUS1004",
                full_name="Sneha Reddy",
                phone="+91 9876543213",
                address_line="Plot 88, Road No. 36, Jubilee Hills",
                city="Hyderabad",
                state="Telangana",
                postal_code="500033",
                address_type="Home",
                is_default=True
            ),
            Address(
                address_id="ADDR1006",
                customer_id="CUS1005",
                full_name="Vikram Singh",
                phone="+91 9876543214",
                address_line="B-104, Green Glen Apartments, Andheri West",
                city="Mumbai",
                state="Maharashtra",
                postal_code="400053",
                address_type="Home",
                is_default=True
            )
        ]
        session.add_all(addresses_data)
        session.flush()

        # 3. Categories
        categories_data = [
            Category(category_id="CAT101", name="Electronics", slug="electronics", description="Smartphones, Laptops, Audio, Wearables & Accessories", icon="bi-laptop", image="https://images.unsplash.com/photo-1498049794561-7780e7231661?w=500&q=80"),
            Category(category_id="CAT102", name="Fashion", slug="fashion", description="Trendy Men's, Women's Apparel, Footwear & Accessories", icon="bi-bag-heart", image="https://images.unsplash.com/photo-1445205170230-053b83016050?w=500&q=80"),
            Category(category_id="CAT103", name="Home", slug="home", description="Kitchen & Home Appliances, Furniture & Decor", icon="bi-house-door", image="https://images.unsplash.com/photo-1513694203232-719a280e022f?w=500&q=80"),
            Category(category_id="CAT104", name="Books", slug="books", description="Programming, Fiction, Business, Education & Non-fiction", icon="bi-book", image="https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=500&q=80"),
            Category(category_id="CAT105", name="Sports", slug="sports", description="Fitness, Gym Gear, Outdoor Camping & Sports Accessories", icon="bi-bicycle", image="https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=500&q=80"),
            Category(category_id="CAT106", name="Beauty", slug="beauty", description="Premium Skincare, Grooming & Personal Care Essentials", icon="bi-stars", image="https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&q=80")
        ]
        session.add_all(categories_data)
        session.flush()

        # 4. Products (57 items across all required subcategories)
        products_raw = [
            # Electronics -> Smartphones
            ("PRD1001", "SpherePhone Pro Max 5G (256GB)", "Flagship smartphone featuring a 6.7-inch OLED 120Hz display, triple 108MP camera array, and 5000mAh battery with 65W fast charge.", "Electronics", "Smartphones", "SphereTech", 79999, 10, 4.8, 142, 25, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&q=80"),
            ("PRD1002", "NovaEdge 12 Prime (128GB)", "Sleek modern smartphone with curved AMOLED screen, AI night photography, and ultra-durable Gorilla Glass protection.", "Electronics", "Smartphones", "Nova", 28999, 15, 4.5, 89, 40, "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=500&q=80"),
            ("PRD1003", "AeroLite 5G Slim Edition", "Ultra-thin, lightweight budget performance smartphone with octa-core processor and dual stereo speakers.", "Electronics", "Smartphones", "Aero", 16499, 8, 4.3, 62, 55, "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=500&q=80"),

            # Electronics -> Laptops
            ("PRD1004", "ZenBook Ultra 14 OLED", "Premium creator laptop with 14-inch 2.8K 90Hz OLED, Intel Core Ultra 7, 16GB LPDDR5X RAM, and 1TB NVMe SSD.", "Electronics", "Laptops", "ZenTech", 84999, 12, 4.9, 110, 18, "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80"),
            ("PRD1005", "ApexPro Gaming Laptop 16\"", "Uncompromised gaming powerhouse powered by RTX 4070 8GB GPU, Ryzen 7 7840HS, 32GB RAM, and 165Hz QHD display.", "Electronics", "Laptops", "Apex", 119999, 15, 4.7, 74, 12, "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&q=80"),
            ("PRD1006", "EcoBook Thin & Light 15.6\"", "Reliable everyday student and office laptop with FHD anti-glare screen, 8GB RAM, 512GB SSD, and 10-hour battery life.", "Electronics", "Laptops", "EcoTech", 44990, 18, 4.4, 215, 30, "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500&q=80"),
            ("PRD1007", "SwiftAir Business Laptop 13.3\"", "Compact magnesium-alloy business ultrabook with fingerprint reader, TPM 2.0 security chip, and backlit keyboard.", "Electronics", "Laptops", "Swift", 48500, 10, 4.6, 95, 22, "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=500&q=80"),

            # Electronics -> Tablets
            ("PRD1008", "SlateVision 11\" 2K Tablet", "Vibrant 2K tablet for streaming and productivity with quad Dolby Atmos speakers and stylus compatibility.", "Electronics", "Tablets", "VisionTech", 24999, 20, 4.5, 68, 35, "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&q=80"),
            ("PRD1009", "SphereTab Ultra with Precision Stylus", "Professional digital drawing and note-taking tablet bundled with magnetic low-latency stylus pen.", "Electronics", "Tablets", "SphereTech", 52999, 10, 4.8, 42, 15, "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=500&q=80"),

            # Electronics -> Headphones
            ("PRD1010", "SoundPulse ANC Wireless Headphones", "Over-ear wireless headphones with active noise cancellation up to 35dB, plush memory foam pads, and 40h battery.", "Electronics", "Headphones", "SoundPulse", 7999, 25, 4.7, 340, 60, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"),
            ("PRD1011", "StudioMaster Pro Audiophile Headphones", "Open-back studio reference headphones delivering neutral acoustic accuracy and wide spatial soundstage.", "Electronics", "Headphones", "MasterSound", 14499, 15, 4.9, 115, 20, "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&q=80"),
            ("PRD1012", "BassVibe Foldable Bluetooth Headset", "Deep punchy bass, built-in hands-free mic, foldable lightweight headband, and convenient USB-C charging.", "Electronics", "Headphones", "BassVibe", 2299, 30, 4.2, 180, 75, "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=500&q=80"),

            # Electronics -> Earbuds
            ("PRD1013", "AirPulse True Wireless ANC Earbuds", "Ergonomic TWS earbuds with hybrid active noise cancellation, ambient transparency mode, and IPX5 water resistance.", "Electronics", "Earbuds", "SoundPulse", 3499, 40, 4.6, 520, 120, "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&q=80"),
            ("PRD1014", "EchoBuds Pro with Spatial Audio", "Crystal clear voice isolation with 6 beamforming microphones, wireless charging case, and personalized sound tuning.", "Electronics", "Earbuds", "EchoTech", 6999, 20, 4.7, 190, 45, "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=500&q=80"),

            # Electronics -> Smart Watches
            ("PRD1015", "ChronoFit Active GPS Smartwatch", "Rugged fitness watch with built-in GPS, SpO2 sensor, continuous heart rate tracking, and 100+ sport modes.", "Electronics", "Smart Watches", "ChronoFit", 4999, 35, 4.5, 430, 90, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80"),
            ("PRD1016", "SphereWatch Elite Sapphire", "Luxury smartwatch crafted from aerospace grade titanium with sapphire crystal glass and ECG capability.", "Electronics", "Smart Watches", "SphereTech", 18999, 15, 4.8, 88, 28, "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&q=80"),

            # Electronics -> Speakers
            ("PRD1017", "SonicBoom Waterproof Bluetooth Speaker", "360-degree room-filling audio, IPX7 submersible design, customizable LED party lights, and 16 hours playtime.", "Electronics", "Speakers", "SonicBoom", 3199, 20, 4.6, 275, 65, "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=500&q=80"),
            ("PRD1018", "HomeAcoustic 5.1 Dolby Soundbar", "Cinema quality soundbar with wireless downward-firing subwoofer and HDMI eARC connectivity.", "Electronics", "Speakers", "AcousticLab", 12999, 25, 4.7, 156, 30, "https://images.unsplash.com/photo-1545127398-14699f92334b?w=500&q=80"),

            # Fashion -> Men's Clothing
            ("PRD1019", "UrbanCraft Slim Fit Oxford Cotton Shirt", "100% combed cotton classic Oxford weave shirt, wrinkle-resistant finish, suitable for formal and casual wear.", "Fashion", "Men's Clothing", "UrbanCraft", 1499, 30, 4.4, 210, 80, "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500&q=80"),
            ("PRD1020", "MetroDenim Tapered Stretch Jeans", "Authentic 5-pocket design made with flexible elastane blend for all-day comfort and modern slim fit silhouette.", "Fashion", "Men's Clothing", "MetroDenim", 1899, 20, 4.5, 175, 60, "https://images.unsplash.com/photo-1542272604-780c96856592?w=500&q=80"),
            ("PRD1021", "AeroFit Breathable Gym T-Shirt", "Quick-dry moisture wicking athletic training t-shirt with anti-odor microbial technology.", "Fashion", "Men's Clothing", "AeroFit", 699, 40, 4.3, 310, 110, "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&q=80"),

            # Fashion -> Women's Clothing
            ("PRD1022", "AuraFlow Floral Chiffon Maxi Dress", "Breezy summer maxi dress with delicate floral prints, elastic smocked waistline, and breathable lining.", "Fashion", "Women's Clothing", "AuraStyle", 2299, 35, 4.7, 160, 45, "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500&q=80"),
            ("PRD1023", "ElegantWeave Silk Blend Kurta Set", "Exquisite festive ethnic kurta set with palazzo pants, gold foil detailing, and matching organza dupatta.", "Fashion", "Women's Clothing", "ElegantWeave", 2999, 25, 4.8, 98, 35, "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=500&q=80"),
            ("PRD1024", "ComfortPlus High-Waist Seamless Leggings", "Buttery soft 4-way stretch non-see-through workout tights with tummy compression band.", "Fashion", "Women's Clothing", "ComfortPlus", 899, 30, 4.6, 240, 85, "https://images.unsplash.com/photo-1506630448388-4e683c67ddb0?w=500&q=80"),

            # Fashion -> Shoes
            ("PRD1025", "VelocityPro Running Shoes Men", "High-performance mesh road runners with responsive nitrogen-infused foam midsole cushioning.", "Fashion", "Shoes", "Velocity", 3499, 25, 4.6, 380, 50, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&q=80"),
            ("PRD1026", "StellaWalk Comfort Leather Loafers Women", "Genuine soft grain leather slip-on loafers with cushioned arch support insole.", "Fashion", "Shoes", "StellaWalk", 2799, 20, 4.5, 120, 30, "https://images.unsplash.com/photo-1535043934128-cf0b28d52f95?w=500&q=80"),
            ("PRD1027", "AirCushion Casual Canvas Sneakers", "Timeless unisex lace-up low-top vulcanized rubber sole sneakers for daily casual walking.", "Fashion", "Shoes", "StreetStyle", 1599, 35, 4.4, 450, 95, "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=500&q=80"),

            # Fashion -> Bags
            ("PRD1028", "NomadTech Water-Resistant Laptop Backpack", "30L commuter travel bag with 15.6\" padded laptop compartment, USB port, and anti-theft back pocket.", "Fashion", "Bags", "NomadTech", 2199, 30, 4.8, 510, 70, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&q=80"),
            ("PRD1029", "Milano Vegan Leather Tote Handbag", "Spacious and chic shoulder tote bag with gold-tone hardware and zippered interior organizers.", "Fashion", "Bags", "Milano", 3299, 15, 4.7, 135, 40, "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500&q=80"),

            # Home -> Kitchen Appliances
            ("PRD1030", "NutriBlend 1000W High-Speed Blender", "Powerful extractor blender with titanium blades, BPA-free smoothie cups, and auto pulse presets.", "Home", "Kitchen Appliances", "NutriBlend", 3899, 20, 4.6, 320, 55, "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=500&q=80"),
            ("PRD1031", "CrispAir Digital 4.5L Air Fryer", "Guilt-free oil-less cooking with rapid air convection technology, 8 one-touch cooking presets, and non-stick basket.", "Home", "Kitchen Appliances", "CrispAir", 5499, 35, 4.7, 460, 40, "https://images.unsplash.com/photo-1585515320310-259814833e62?w=500&q=80"),
            ("PRD1032", "AromaBrew Espresso & Cappuccino Maker", "15-bar Italian pressure pump machine with stainless steel milk steam frother wand.", "Home", "Kitchen Appliances", "AromaBrew", 8999, 22, 4.5, 180, 25, "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=500&q=80"),

            # Home -> Home Appliances
            ("PRD1033", "PureBreeze True HEPA Room Air Purifier", "3-stage filtration capturing 99.97% dust, smoke, and allergens with real-time PM2.5 display indicator.", "Home", "Home Appliances", "PureBreeze", 7499, 25, 4.8, 290, 35, "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=500&q=80"),
            ("PRD1034", "AquaShield Smart UV+RO Water Purifier", "8-stage purification with mineral boost infusion, TDS controller, and 7L storage tank.", "Home", "Home Appliances", "AquaShield", 11999, 20, 4.6, 210, 20, "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=500&q=80"),
            ("PRD1035", "RobotVac Smart Laser Navigation Vacuum", "Automated 2-in-1 sweeping and mopping robot with LiDAR room mapping and app boundary control.", "Home", "Home Appliances", "RobotVac", 19999, 30, 4.7, 140, 15, "https://images.unsplash.com/photo-1518640467707-6811f4a6ab73?w=500&q=80"),

            # Home -> Furniture
            ("PRD1036", "Ergonomic Mesh High-Back Office Chair", "Breathable backrest with adjustable lumbar support, 3D armrests, and recline lock mechanism.", "Home", "Furniture", "ErgoComfort", 8499, 25, 4.8, 380, 30, "https://images.unsplash.com/photo-1580481077195-c3a821a58875?w=500&q=80"),
            ("PRD1037", "Nordic Wood Minimalist Coffee Table", "Engineered solid pine wood center table with natural grain finish and open lower magazine shelf.", "Home", "Furniture", "NordicHome", 4999, 15, 4.4, 90, 20, "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=500&q=80"),

            # Home -> Home Accessories
            ("PRD1038", "LuminaTouch Adjustable LED Desk Lamp", "Flicker-free eye caring lamp with 5 color temperatures, brightness dimmer, and wireless charging pad base.", "Home", "Home Accessories", "Lumina", 1299, 30, 4.5, 230, 80, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500&q=80"),
            ("PRD1039", "CozyCloud Memory Foam Cervical Pillow", "Ergonomic contour design for neck pain relief with cooling bamboo fiber washable cover.", "Home", "Home Accessories", "CozyCloud", 1499, 20, 4.6, 175, 60, "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=500&q=80"),

            # Books -> Programming
            ("PRD1040", "Mastering Python & Modern Software Architecture", "In-depth handbook on clean code patterns, asynchronous programming, microservices, and testing best practices.", "Books", "Programming", "TechPress", 1250, 10, 4.9, 520, 150, "https://images.unsplash.com/photo-1532012164546-f432f2e3777f?w=500&q=80"),
            ("PRD1041", "Designing Data-Intensive Distributed Systems", "Essential guide for engineers on reliability, scalability, partitioning, replication, and consensus protocols.", "Books", "Programming", "O'Reilly-Sphere", 1850, 15, 4.9, 640, 120, "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&q=80"),
            ("PRD1042", "Deep Learning & Large Language Models in Practice", "Practical guide to transformer architectures, fine-tuning, RAG pipelines, and agentic workflows.", "Books", "Programming", "AI Frontiers", 1999, 12, 4.8, 310, 80, "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=500&q=80"),

            # Books -> Fiction
            ("PRD1043", "The Chrono Paradox: A Sci-Fi Thriller", "A gripping time-travel narrative exploring alternate realities, quantum espionage, and the fate of civilization.", "Books", "Fiction", "NovaReads", 499, 20, 4.6, 180, 100, "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=500&q=80"),
            ("PRD1044", "Shadows Over Solitude: Detective Mystery", "Page-turning crime novel following detective Arjun Sen through a locked-room murder in misty hills.", "Books", "Fiction", "SilverInk", 399, 25, 4.5, 140, 90, "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=500&q=80"),

            # Books -> Education
            ("PRD1045", "Advanced Engineering Mathematics & Algorithms", "Comprehensive textbook covering linear algebra, differential calculus, numerical optimization, and graphs.", "Books", "Education", "AcademicSphere", 850, 10, 4.7, 95, 60, "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=500&q=80"),

            # Books -> Business
            ("PRD1046", "The Zero-to-One Growth Blueprint", "Strategies for startup founders on product-market fit, unit economics, viral loops, and scaling companies.", "Books", "Business", "ApexBooks", 650, 15, 4.7, 230, 75, "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=500&q=80"),
            ("PRD1047", "Strategic Thinking & Executive Decision Making", "Frameworks for leaders navigating market disruption, risk management, and competitive advantage.", "Books", "Business", "ExecutivePress", 720, 10, 4.6, 110, 50, "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=500&q=80"),

            # Sports -> Fitness
            ("PRD1048", "FlexGrip Adjustable Dumbbell Set (2.5kg - 20kg)", "Space-saving dumbbell with selector dial system replacing 10 pairs of traditional weights.", "Sports", "Fitness", "FlexGrip", 4599, 20, 4.8, 320, 40, "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=500&q=80"),
            ("PRD1049", "ProBalance Non-Slip 8mm Yoga Mat", "High density eco-friendly TPE mat with laser alignment lines and moisture-proof carry strap.", "Sports", "Fitness", "ProBalance", 1199, 30, 4.6, 410, 80, "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&q=80"),

            # Sports -> Outdoor
            ("PRD1050", "TrailBlazer 4-Person Waterproof Camping Tent", "Quick setup dome tent with 3000mm hydrostatic head rainfly and dual ventilation mesh windows.", "Sports", "Outdoor", "TrailBlazer", 6499, 25, 4.7, 125, 25, "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=500&q=80"),
            ("PRD1051", "PolarThermal 1L Insulated Sports Flask", "Double-wall vacuum flask keeping beverages iced cold for 24 hours or steaming hot for 12 hours.", "Sports", "Outdoor", "PolarThermal", 899, 20, 4.8, 590, 130, "https://images.unsplash.com/photo-1523362628745-0c100150b504?w=500&q=80"),

            # Sports -> Sports Accessories
            ("PRD1052", "SpeedRope Pro Aluminium Skipping Rope", "360-degree ball bearing jump rope with adjustable steel cable for HIIT and cardio conditioning.", "Sports", "Sports Accessories", "SpeedRope", 449, 25, 4.5, 340, 110, "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=500&q=80"),

            # Beauty -> Skincare
            ("PRD1053", "RadiantGlow 15% Vitamin C + Ferulic Serum", "Brightening facial serum targeting dark spots, collagen synthesis, and sun damage defense.", "Beauty", "Skincare", "RadiantGlow", 799, 20, 4.7, 480, 95, "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&q=80"),
            ("PRD1054", "HydraSurge Ultra Lightweight Gel Moisturizer", "Oil-free hyaluronic acid moisturizer providing 72-hour continuous hydration without clogging pores.", "Beauty", "Skincare", "HydraSurge", 599, 15, 4.6, 350, 105, "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&q=80"),
            ("PRD1055", "UV-Shield Invisible Broad Spectrum SPF 50", "Ultra-sheer zero white-cast daily sunscreen protecting against UVA, UVB, and blue light.", "Beauty", "Skincare", "UV-Shield", 499, 10, 4.8, 620, 140, "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&q=80"),

            # Beauty -> Personal Care
            ("PRD1056", "SonicClean Ultrasonic Electric Toothbrush", "40,000 vibrations/min motor, 5 brushing modes, quad-pacer 2-minute timer, and 30-day battery life.", "Beauty", "Personal Care", "SonicClean", 1899, 30, 4.7, 270, 50, "https://images.unsplash.com/photo-1559591937-e10b1062f8b5?w=500&q=80"),
            ("PRD1057", "KeratinPro Moisture Repair Hair Mask", "Deep conditioning treatment infused with argan oil and hydrolyzed keratin for silky frizz-free hair.", "Beauty", "Personal Care", "KeratinPro", 699, 20, 4.6, 210, 70, "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=500&q=80")
        ]

        products_objects = []
        for p in products_raw:
            price = Decimal(str(p[6]))
            disc = Decimal(str(p[7]))
            final_price = round(price * (Decimal("1.0") - (disc / Decimal("100.0"))), 2)
            products_objects.append(
                Product(
                    product_id=p[0],
                    product_name=p[1],
                    description=p[2],
                    category=p[3],
                    subcategory=p[4],
                    brand=p[5],
                    price=price,
                    discount=disc,
                    final_price=final_price,
                    rating=Decimal(str(p[8])),
                    review_count=p[9],
                    stock_quantity=p[10],
                    seller="ShopSphere Retail Ltd.",
                    image=p[11],
                    status="ACTIVE",
                    created_at=datetime.utcnow() - timedelta(days=120)
                )
            )
        session.add_all(products_objects)
        session.flush()

        # 5. Orders (22 comprehensive seeded orders across all lifecycle states)
        orders_data = [
            # 1. PLACED (Freshly placed order, fully cancellable)
            ("ORD1001", "CUS1001", 1, 3499.00, 349.90, 3149.10, "PLACED", "NONE", "NONE", "ADDR1001", "PRD1013", "AirPulse True Wireless ANC Earbuds", 1, 3149.10),
            # 2. CONFIRMED (Confirmed by seller, cancellable)
            ("ORD1002", "CUS1001", 3, 44990.00, 8098.20, 36891.80, "CONFIRMED", "NONE", "NONE", "ADDR1001", "PRD1006", "EcoBook Thin & Light 15.6\"", 1, 36891.80),
            # 3. PACKED (Packed in warehouse, cancellation restricted)
            ("ORD1003", "CUS1001", 5, 4999.00, 1749.65, 3249.35, "PACKED", "NONE", "NONE", "ADDR1002", "PRD1015", "ChronoFit Active GPS Smartwatch", 1, 3249.35),
            # 4. SHIPPED (In transit, non-cancellable)
            ("ORD1004", "CUS1001", 7, 7999.00, 1999.75, 5999.25, "SHIPPED", "NONE", "NONE", "ADDR1001", "PRD1010", "SoundPulse ANC Wireless Headphones", 1, 5999.25),
            # 5. OUT_FOR_DELIVERY (On delivery van)
            ("ORD1005", "CUS1001", 9, 2199.00, 659.70, 1539.30, "OUT_FOR_DELIVERY", "NONE", "NONE", "ADDR1001", "PRD1028", "NomadTech Water-Resistant Laptop Backpack", 1, 1539.30),
            # 6. DELIVERED (Delivered recently, eligible for return/refund)
            ("ORD1006", "CUS1001", 12, 5499.00, 1924.65, 3574.35, "DELIVERED", "NONE", "NONE", "ADDR1001", "PRD1031", "CrispAir Digital 4.5L Air Fryer", 1, 3574.35),
            # 7. CANCELLED (User cancelled order)
            ("ORD1007", "CUS1001", 15, 1299.00, 389.70, 909.30, "CANCELLED", "CANCELLED_BY_CUSTOMER", "NONE", "ADDR1001", "PRD1038", "LuminaTouch Adjustable LED Desk Lamp", 1, 909.30),
            # 8. RETURN_REQUESTED (Return requested)
            ("ORD1008", "CUS1001", 18, 3499.00, 874.75, 2624.25, "RETURN_REQUESTED", "NONE", "REQUESTED", "ADDR1001", "PRD1025", "VelocityPro Running Shoes Men", 1, 2624.25),
            # 9. REFUNDED (Already refunded order, testing repeat refund attempts)
            ("ORD1009", "CUS1001", 25, 4599.00, 919.80, 3679.20, "REFUNDED", "NONE", "PROCESSED", "ADDR1001", "PRD1048", "FlexGrip Adjustable Dumbbell Set 20KG", 1, 3679.20),
            # 10. HIGH VALUE DELIVERED ORDER (> ₹1,00,000, testing escalation)
            ("ORD1010", "CUS1001", 30, 119999.00, 17999.85, 101999.15, "DELIVERED", "NONE", "NONE", "ADDR1001", "PRD1005", "ApexPro Gaming Laptop 16\"", 1, 101999.15),
            # 11. Priya - PLACED
            ("ORD1011", "CUS1002", 2, 2299.00, 804.65, 1494.35, "PLACED", "NONE", "NONE", "ADDR1003", "PRD1022", "AuraFlow Floral Chiffon Maxi Dress", 1, 1494.35),
            # 12. Priya - DELIVERED
            ("ORD1012", "CUS1002", 14, 799.00, 159.80, 639.20, "DELIVERED", "NONE", "NONE", "ADDR1003", "PRD1053", "RadiantGlow Vitamin C + Ferulic Serum", 1, 639.20),
            # 13. Priya - SHIPPED
            ("ORD1013", "CUS1002", 6, 2999.00, 749.75, 2249.25, "SHIPPED", "NONE", "NONE", "ADDR1003", "PRD1023", "ElegantWeave Silk Blend Kurta Set", 1, 2249.25),
            # 14. Priya - RETURNED
            ("ORD1014", "CUS1002", 28, 3299.00, 494.85, 2804.15, "RETURNED", "NONE", "PROCESSED", "ADDR1003", "PRD1029", "Milano Vegan Leather Tote Handbag", 1, 2804.15),
            # 15. Amit - DELIVERED
            ("ORD1015", "CUS1003", 10, 1250.00, 125.00, 1125.00, "DELIVERED", "NONE", "NONE", "ADDR1004", "PRD1040", "Mastering Python & Modern Software Architecture", 1, 1125.00),
            # 16. Amit - CANCELLED
            ("ORD1016", "CUS1003", 12, 1850.00, 277.50, 1572.50, "CANCELLED", "CANCELLED_BY_CUSTOMER", "NONE", "ADDR1004", "PRD1041", "Designing Data-Intensive Distributed Systems", 1, 1572.50),
            # 17. Amit - CONFIRMED
            ("ORD1017", "CUS1003", 1, 7499.00, 1874.75, 5624.25, "CONFIRMED", "NONE", "NONE", "ADDR1004", "PRD1033", "PureBreeze HEPA Room Air Purifier", 1, 5624.25),
            # 18. Sneha - DELIVERED
            ("ORD1018", "CUS1004", 16, 1899.00, 569.70, 1329.30, "DELIVERED", "NONE", "NONE", "ADDR1005", "PRD1056", "SonicClean Ultrasonic Electric Toothbrush", 1, 1329.30),
            # 19. Sneha - SHIPPED
            ("ORD1019", "CUS1004", 4, 1199.00, 359.70, 839.30, "SHIPPED", "NONE", "NONE", "ADDR1005", "PRD1049", "ProBalance Non-Slip 8mm Yoga Mat", 1, 839.30),
            # 20. Sneha - PLACED
            ("ORD1020", "CUS1004", 2, 499.00, 49.90, 449.10, "PLACED", "NONE", "NONE", "ADDR1005", "PRD1055", "UV-Shield Broad Spectrum SPF 50", 1, 449.10),
            # 21. Vikram - DELIVERED
            ("ORD1021", "CUS1005", 22, 6499.00, 1624.75, 4874.25, "DELIVERED", "NONE", "NONE", "ADDR1006", "PRD1050", "TrailBlazer 4-Person Waterproof Camping Tent", 1, 4874.25),
            # 22. Vikram - PACKED
            ("ORD1022", "CUS1005", 3, 3199.00, 639.80, 2559.20, "PACKED", "NONE", "NONE", "ADDR1006", "PRD1017", "SonicBoom Waterproof Bluetooth Speaker", 1, 2559.20)
        ]

        for idx, item in enumerate(orders_data, start=1):
            order_id = item[0]
            cust_id = item[1]
            days_ago = item[2]
            subtot = Decimal(str(item[3]))
            disc = Decimal(str(item[4]))
            tot = Decimal(str(item[5]))
            o_status = item[6]
            c_status = item[7]
            r_status = item[8]
            addr_id = item[9]
            prod_id = item[10]
            prod_name = item[11]
            qty = item[12]
            item_tot = Decimal(str(item[13]))

            order_time = datetime.utcnow() - timedelta(days=days_ago)

            order = Order(
                order_id=order_id,
                customer_id=cust_id,
                order_date=order_time,
                subtotal=subtot,
                discount=disc,
                total_amount=tot,
                payment_id=f"PAY{idx:04d}",
                delivery_id=f"DEL{idx:04d}",
                order_status=o_status,
                cancellation_status=c_status,
                refund_status=r_status,
                shipping_address_id=addr_id,
                shipping_address_text="Sunshine Heights, MG Road, Bengaluru, Karnataka - 560001"
            )
            session.add(order)
            session.flush()

            # Order Item
            order_item = OrderItem(
                item_id=f"OITM{idx:04d}",
                order_id=order_id,
                product_id=prod_id,
                product_name=prod_name,
                quantity=qty,
                unit_price=item_tot / qty,
                total_price=item_tot,
                image="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"
            )
            session.add(order_item)

            # Payment
            payment_status = "REFUNDED" if o_status == "REFUNDED" else ("FAILED" if o_status == "CANCELLED" and days_ago > 20 else "COMPLETED")
            payment_method = "UPI" if idx % 3 == 0 else ("Credit Card" if idx % 2 == 0 else "Cash on Delivery")
            payment = Payment(
                payment_id=f"PAY{idx:04d}",
                order_id=order_id,
                payment_method=payment_method,
                amount=tot,
                payment_status=payment_status,
                transaction_id=f"TXN{98204910 + idx}",
                created_at=order_time
            )
            session.add(payment)

            # Delivery
            deliv_status = "DELIVERED" if o_status in ["DELIVERED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"] else (
                "OUT_FOR_DELIVERY" if o_status == "OUT_FOR_DELIVERY" else (
                    "SHIPPED" if o_status == "SHIPPED" else (
                        "PROCESSING" if o_status in ["CONFIRMED", "PACKED"] else "PENDING"
                    )
                )
            )
            current_loc = "Local Delivery Hub, Bengaluru" if deliv_status == "OUT_FOR_DELIVERY" else (
                "Destination Address" if deliv_status == "DELIVERED" else "Central Logistics Hub, Pune"
            )
            delivery = Delivery(
                delivery_id=f"DEL{idx:04d}",
                order_id=order_id,
                tracking_number=f"TRK{89201900 + idx}",
                carrier="SphereExpress",
                delivery_status=deliv_status,
                estimated_delivery=order_time + timedelta(days=3),
                current_location=current_loc,
                shipped_at=order_time + timedelta(days=1) if o_status in ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"] else None,
                delivered_at=order_time + timedelta(days=3) if o_status in ["DELIVERED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"] else None
            )
            session.add(delivery)

            # Return & Refund records if applicable
            if o_status in ["RETURN_REQUESTED", "RETURNED"]:
                ret = Return(
                    return_id=f"RET{idx:04d}",
                    order_id=order_id,
                    customer_id=cust_id,
                    reason="Size issue - fits slightly tighter than expected",
                    return_status="REQUESTED" if o_status == "RETURN_REQUESTED" else "COMPLETED",
                    requested_at=order_time + timedelta(days=4)
                )
                session.add(ret)

            if o_status in ["REFUNDED", "RETURNED"]:
                ref = Refund(
                    refund_id=f"REF{idx:04d}",
                    order_id=order_id,
                    payment_id=f"PAY{idx:04d}",
                    amount=tot,
                    refund_status="PROCESSED",
                    processed_at=order_time + timedelta(days=5)
                )
                session.add(ref)

        session.commit()
        print("[Database] Successfully seeded 5 customers, 6 categories, 57 products, and 22 realistic orders!")

    except Exception as e:
        session.rollback()
        print(f"[Database Error] Seeding failed: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    init_database()

